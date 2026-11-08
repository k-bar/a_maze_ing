import heapq
from typing import Generator

from ..utils import Direction
from .base_solver import MazeSolver

class AStarSolver(MazeSolver):

    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:

        maze_walls = self.maze.get_walls()
        width = self.maze.width
        # height = self.maze.height

        locked_mask = self.maze.locked_cells_mask
        border_mask = self.maze.border_masks

        start_idx = self.maze.m_entry[1] * width + self.maze.m_entry[0]
        exit_idx = self.maze.m_exit[1] * width + self.maze.m_exit[0]

        def manhattan_distance(idx_a: int, idx_b: int) -> int:
            return (abs((idx_a % width) - (idx_b % width))
                    + abs((idx_a // width) - (idx_b // width)))

        # f_score (total_cost) = g_score (moves_done) + h_score (manhattan_distance)
        # unique counter
        # current
        queue: list[tuple[int, int, int]] = []
        count = 0

        start_f_score = manhattan_distance(start_idx, exit_idx)

        # initial state, cost: 0 moves + manhattan
        heapq.heappush(queue, (start_f_score, count, start_idx))

        # structure of graph: current -> parent
        came_from: dict[int, int | None] = {start_idx: None}

        # real cost of getting moves for each state (state > moves number)
        g_score: dict[int, int] = {start_idx: 0}

        while queue:

            # get state with the lowest cost
            _, _, current_idx = heapq.heappop(queue)

            if current_idx == exit_idx:
                path = []
                curr: int | None = exit_idx

                while curr is not None:
                    path.append((curr % width, curr // width))
                    curr = came_from[curr]
                path.reverse()
                self.maze.path = path
                break

            current_cell_bit = 1 << current_idx
            cx, cy = current_idx % width, current_idx // width

            for direction in Direction:

                bit_idx = direction.bit_index

                if (maze_walls[bit_idx] | border_mask[
                    bit_idx]) & current_cell_bit:
                    continue

                next_idx = current_idx + (width * direction.dy) + direction.dx

                if (1 << next_idx) & locked_mask:
                    continue

                #
                # nx = cx + direction.dx
                # ny = cy + direction.dy
                #
                # if 0 < nx < width and 0 < ny < height:
                #     next_idx = ny * width + nx
                #
                #     if next_idx in locked_indices:
                #         continue

                tentative_g_score = g_score[current_idx] + 1

                if next_idx not in g_score or tentative_g_score < g_score[
                    next_idx]:
                    came_from[next_idx] = current_idx
                    g_score[next_idx] = tentative_g_score

                    yield next_idx % width, next_idx // width, direction

                    f_score = tentative_g_score + manhattan_distance(
                        next_idx, exit_idx)
                    count += 1
                    heapq.heappush(queue, (f_score, count, next_idx))
