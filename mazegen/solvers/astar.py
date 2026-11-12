import heapq
from typing import Generator

from ..utils import Direction
from .base_solver import MazeSolver


class AStarSolver(MazeSolver):
    """
    A maze solver that implements the A* (A-Star) search algorithm.

    This solver uses the Manhattan distance as its heuristic function to
    efficiently find the shortest path from the maze's entry to its exit.
    It leverages bitwise operations for fast collision detection against maze
    walls and locked cells.
    """

    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        """
        Executes the main loop of the A* algorithm to solve the maze.

        The method explores the maze using a priority queue to evaluate the
        most promising paths first, based on the cost to reach the current
        cell (g-score) plus the estimated heuristic cost to the exit (h-score).
        It yields each explored step to allow for real-time tracking or
        visualization of the exploration process.

        Yields:
            tuple[int, int, Direction]: A tuple containing the x-coordinate,
            y-coordinate, and the direction taken to reach the newly explored
            cell.
        """

        width = self.maze.width
        locked_mask = self.maze.locked_cells_mask

        start_idx = self.maze.m_entry[1] * width + self.maze.m_entry[0]
        exit_idx = self.maze.m_exit[1] * width + self.maze.m_exit[0]
        exit_x = exit_idx % width
        exit_y = exit_idx // width

        directions_map = self._get_directions_map()

        start_f_score = abs((start_idx % width) - exit_x) + abs(
            (start_idx // width) - exit_y
        )
        queue: list[tuple[int, int, int]] = [(start_f_score, 0, start_idx)]
        came_from: dict[int, int] = {}
        g_score: dict[int, int] = {start_idx: 0}
        count = 0

        while queue:
            f_val, _, current_idx = heapq.heappop(queue)

            if current_idx == exit_idx:
                self._reconstruct_path(came_from, start_idx, exit_idx)
                break

            curr_g = g_score[current_idx]
            curr_h = abs((current_idx % width) - exit_x) + abs(
                (current_idx // width) - exit_y
            )
            if f_val > curr_g + curr_h:
                continue

            current_cell_bit = 1 << current_idx
            tentative_g = curr_g + 1

            for direction, blocked_mask, offset in directions_map:
                if blocked_mask & current_cell_bit:
                    continue

                next_idx = current_idx + offset
                if (1 << next_idx) & locked_mask:
                    continue

                if next_idx not in g_score or tentative_g < g_score[next_idx]:
                    came_from[next_idx] = current_idx
                    g_score[next_idx] = tentative_g

                    nx = next_idx % width
                    ny = next_idx // width
                    yield nx, ny, direction

                    f_score = tentative_g + abs(nx - exit_x) + abs(ny - exit_y)
                    count += 1
                    heapq.heappush(queue, (f_score, count, next_idx))
