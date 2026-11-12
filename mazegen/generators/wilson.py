"""
Wilson's algorithm maze generator.

This module provides an implementation of Wilson's algorithm for maze
generation.
Wilson's algorithm uses loop-erased random walks to guarantee a mathematically
unbiased maze (a uniform spanning tree).
"""
import random
from dataclasses import dataclass
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class WilsonContext:
    """
    A data class holding the shared state context for the Wilson generator.

    Attributes:
        untouched_cells: Bitmask representing cells not yet part of the maze.
        max_cells: The total number of cells in the maze.
        locked_mask: Bitmask of cells that are locked and cannot be carved.
        directions_map: A tuple mapping direction bit indices to flat grid
        offsets.
    """
    untouched_cells: int
    max_cells: int
    locked_mask: int
    directions_map: tuple[tuple[int, int], ...]


class WilsonGenerator(BaseGenerator):
    """
    Maze generator utilizing Wilson's algorithm.

    This generator builds the maze by performing random walks from an untouched
    cell until it hits a cell already in the maze. If the path loops on itself,
    the loop is erased. Once a valid path is found, it is carved into the maze.
    """

    def _setup_shared_state(self) -> WilsonContext:
        """
        Initializes and retrieves the shared state required for the algorithm.

        Returns:
            WilsonContext: The data context containing initialization
            parameters and bitmasks for the maze grid.
        """
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
        """
        Step-by-step generation loop of Wilson's algorithm for visualization.

        This generator yields each wall manipulation step. It simulates the
        random walk and visually backtracks (restores walls) when a loop is
        detected, making it suitable for animating the loop-erasure process.

        Yields:
            tuple[int, int, Direction]: A tuple containing the coordinates
            and the direction of the wall being modified.
        """

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
        """
        Instant generation of the maze using Wilson's algorithm.

        Unlike `_algorithm_loop`, this method performs the loop-erased random
        walk purely in memory by tracking exit directions for each cell.
        It only carves the walls once a valid path to the maze is finalized,
        making it significantly faster.
        """

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
