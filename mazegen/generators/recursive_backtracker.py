import random
from dataclasses import dataclass
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class BacktrackerState:
    """
    Stores the internal state of the recursive backtracking algorithm.

    Attributes:
        untouched_set (set[int]): A set of flat indices representing unvisited
        cells.
        path (list[int]): A stack of cell indices representing the current
        path, used for backtracking.
        directions_map (tuple[tuple[int, int], ...]): A mapping of direction
        bit indices to their 1D array offsets.
    """
    untouched_set: set[int]
    path: list[int]
    directions_map: tuple[tuple[int, int], ...]


class RecursiveBacktracker(BaseGenerator):
    """
    Generates a maze using the randomized depth-first search (recursive
    backtracking) algorithm.

    This algorithm carves paths by randomly choosing unvisited neighbors.
    If it reaches a dead end, it backtracks along the path until it finds
    a cell with unvisited neighbors.
    """

    def _setup_shared_state(self) -> BacktrackerState:
        """
        Initializes and returns the shared state required for the backtracking
        algorithm.

        This setup accounts for locked cells and the starting cell, ensuring
        they are removed from the untouched set before the algorithm begins.

        Returns:
            BacktrackerState: The initialized state object.
        """
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
        """
        Executes the recursive backtracking algorithm step-by-step.

        This is a generator method primarily used for visualizing the maze
        generation process. It yields the state of the maze after each
        successful wall removal.

        Yields:
            tuple[int, int, Direction]: A tuple containing the start cell
            index, the next cell index, and the direction of the move.
        """

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
        """
        Executes the recursive backtracking algorithm to completion instantly.

        Unlike `_algorithm_loop`, this method does not yield intermediate
        steps, making it significantly faster for generating a complete maze
        when visualization is not required.
        """

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
