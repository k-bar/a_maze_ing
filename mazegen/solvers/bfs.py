from collections import deque
from typing import Generator

from ..utils import Direction
from .base_solver import MazeSolver


class BFSSolver(MazeSolver):
    """A maze solver implementing the Breadth-First Search (BFS) algorithm.

    This solver explores the maze systematically level by level, ensuring that
    the shortest path from the entry to the exit is found in an unweighted
    grid. It leverages 1D coordinate indexing and integer bitmasks to
    efficiently track locked cells and navigate boundaries.
    """

    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Execute the BFS pathfinding loop.

        Traverses the maze starting from the entry point, maintaining a queue
        of cells to visit. It yields the state of each valid step taken during
        the search, which can be used for step-by-step visualization or
        debugging. Once the exit is reached, it triggers the internal path
        reconstruction.

        Yields:
            tuple[int, int, Direction]: A tuple containing the newly visited
            cell's x-coordinate, y-coordinate, and the direction moved to
            reach it.

        Returns:
            None: The generator completes either when the exit cell is reached
            and the path is reconstructed, or when all reachable cells are
            exhausted.
        """

        width = self.maze.width
        locked_mask = self.maze.locked_cells_mask
        start_idx = self.maze.m_entry[1] * width + self.maze.m_entry[0]
        exit_idx = self.maze.m_exit[1] * width + self.maze.m_exit[0]

        directions_map = self._get_directions_map()

        queue: deque[int] = deque([start_idx])
        visited: set[int] = {start_idx}
        came_from: dict[int, int] = {}

        if start_idx == exit_idx:
            self._reconstruct_path(came_from, start_idx, exit_idx)
            return

        while queue:
            current_idx = queue.popleft()
            current_cell_bit = 1 << current_idx

            for direction, blocked_mask, offset in directions_map:
                if blocked_mask & current_cell_bit:
                    continue

                next_idx = current_idx + offset
                if next_idx in visited or ((1 << next_idx) & locked_mask):
                    continue

                visited.add(next_idx)
                came_from[next_idx] = current_idx
                queue.append(next_idx)

                yield next_idx % width, next_idx // width, direction

                if next_idx == exit_idx:
                    self._reconstruct_path(came_from, start_idx, exit_idx)
                    return
