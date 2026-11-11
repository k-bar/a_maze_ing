import random
from dataclasses import dataclass
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class WilsonContext:
    untouched_cells: int
    max_cells: int
    locked_mask: int
    directions_map: tuple[tuple[int, int], ...]


class WilsonGenerator(BaseGenerator):

    def _setup_shared_state(self) -> WilsonContext:
        untouched_cells, _, max_cells = self._initialize_generator()
        width = self.maze.width
        directions_map = tuple(
            (d.bit_index, d.get_flat_offset(width)) for d in Direction
        )
        return WilsonContext(
            untouched_cells=untouched_cells,
            max_cells=max_cells,
            locked_mask=self.maze.locked_cells_mask,
            directions_map=directions_map,
        )

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:

        ctx = self._setup_shared_state()
        untouched_cells = ctx.untouched_cells
        max_cells = ctx.max_cells
        locked_mask = ctx.locked_mask
        directions_map = ctx.directions_map
        border_masks = self.maze.border_masks

        while untouched_cells:
            start_cell = self.maze.pick_random_cell(mask=untouched_cells,
                                                    max_cells=max_cells)

            current_path = [start_cell]
            current_path_mask = (1 << start_cell)
            while True:
                current_cell = current_path[-1]
                cell_bit = 1 << current_cell
                moves = [
                    offset for bit_idx, offset in directions_map
                    if not (border_masks[bit_idx] & cell_bit) and not (
                            locked_mask & (1 << (current_cell + offset)))
                ]
                offset = random.choice(moves)
                next_cell = current_cell + offset

                # part of maze:
                if not untouched_cells & (1 << next_cell):
                    self.maze.flip_both_walls(current_cell, next_cell)
                    yield self.maze.get_coords_and_dir(current_cell, next_cell)
                    while current_path:
                        cell = current_path.pop()
                        untouched_cells &= ~(1 << cell)
                    break
                # backtrack if loop
                elif current_path_mask & (1 << next_cell):
                    while current_path[-1] != next_cell:
                        removed = current_path.pop()
                        current_path_mask &= ~(1 << removed)
                        previous_cell = current_path[-1]
                        self.maze.flip_both_walls(removed, previous_cell)
                        yield self.maze.get_coords_and_dir(removed,
                                                           previous_cell)
                # normal wandering
                else:
                    current_path.append(next_cell)
                    current_path_mask |= (1 << next_cell)
                    self.maze.flip_both_walls(current_cell, next_cell)
                    yield self.maze.get_coords_and_dir(current_cell, next_cell)

    def generate_all(self) -> None:

        ctx = self._setup_shared_state()
        untouched_cells = ctx.untouched_cells
        max_cells = ctx.max_cells
        locked_mask = ctx.locked_mask
        directions_map = ctx.directions_map
        border_masks = self.maze.border_masks

        cell_directions: dict[int, int] = {}
        while untouched_cells:
            start_cell = self.maze.pick_random_cell(mask=untouched_cells,
                                                    max_cells=max_cells)
            current_cell = start_cell
            while untouched_cells & (1 << current_cell):
                cell_bit = 1 << current_cell
                moves = [
                    offset for bit_idx, offset in directions_map
                    if not (border_masks[bit_idx] & cell_bit) and not (
                            locked_mask & (1 << (current_cell + offset)))
                ]
                offset = random.choice(moves)
                cell_directions[current_cell] = offset
                current_cell += offset

            carve_cell = start_cell
            while untouched_cells & (1 << carve_cell):
                next_carve_cell = carve_cell + cell_directions[carve_cell]
                self.maze.flip_both_walls(carve_cell, next_carve_cell)

                untouched_cells &= ~(1 << carve_cell)
                carve_cell = next_carve_cell
            cell_directions.clear()
