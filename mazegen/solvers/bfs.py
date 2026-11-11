from collections import deque
from typing import Generator

from ..utils import Direction
from .base_solver import MazeSolver


class BFSSolver(MazeSolver):

    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Find shortest path from ENTRY to EXIT using Breadth-First Search."""
        maze_walls = self.maze.get_walls()
        border_mask = self.maze.border_masks
        width = self.maze.width
        locked_mask = self.maze.locked_cells_mask

        start_idx = self.maze.m_entry[1] * width + self.maze.m_entry[0]
        exit_idx = self.maze.m_exit[1] * width + self.maze.m_exit[0]

        directions_map = tuple(
            (
                d,
                maze_walls[d.bit_index] | border_mask[d.bit_index],
                d.get_flat_offset(width),
            )
            for d in Direction
        )

        queue: deque[int] = deque([start_idx])
        visited: set[int] = {start_idx}
        came_from: dict[int, int] = {}

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
