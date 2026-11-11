import random
from dataclasses import dataclass
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class BacktrackerState:
    untouched_set: set[int]
    path: list[int]
    directions_map: tuple[tuple[int, int], ...]


class RecursiveBacktracker(BaseGenerator):

    def _setup_shared_state(self) -> BacktrackerState:
        untouched_mask, start_cell, max_cells = self._initialize_generator()
        width = self.maze.width
        directions_map = tuple(
            (d.bit_index, d.get_flat_offset(width)) for d in Direction
        )
        locked_indices = {y * width + x for x, y in self.maze.locked_cells}
        locked_indices.add(start_cell)
        untouched_set = set(range(max_cells)) - locked_indices
        return BacktrackerState(
            untouched_set=untouched_set,
            path=[start_cell],
            directions_map=directions_map,
        )

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:

        state = self._setup_shared_state()
        untouched_set = state.untouched_set
        path = state.path
        directions_map = state.directions_map
        border_masks = self.maze.border_masks

        while untouched_set and path:
            current_cell = path[-1]
            cell_bit = 1 << current_cell
            moves = [
                current_cell + offset for bit_idx, offset in directions_map
                if not (border_masks[bit_idx] & cell_bit)
                and (current_cell + offset) in untouched_set
            ]

            if moves:
                # add cell to path and maze
                next_cell = random.choice(moves)
                untouched_set.remove(next_cell)
                self.maze.flip_both_walls(current_cell, next_cell)
                path.append(next_cell)
                yield self.maze.get_coords_and_dir(current_cell, next_cell)
            # no possible moves, backtrack:
            else:
                path.pop()

    def generate_all(self) -> None:

        state = self._setup_shared_state()
        untouched_set = state.untouched_set
        path = state.path
        directions_map = state.directions_map
        border_masks = self.maze.border_masks

        while untouched_set and path:
            current_cell = path[-1]
            cell_bit = 1 << current_cell
            moves = [
                current_cell + offset for bit_idx, offset in directions_map
                if not (border_masks[bit_idx] & cell_bit)
                and (current_cell + offset) in untouched_set
            ]

            if moves:
                next_cell = random.choice(moves)
                untouched_set.remove(next_cell)
                self.maze.flip_both_walls(current_cell, next_cell)
                path.append(next_cell)
            else:
                path.pop()
