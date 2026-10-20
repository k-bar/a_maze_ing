from collections import deque
from typing import Generator

from . import MazeSolver
from ..utils import Direction


class BFSSolver(MazeSolver):

    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Find corridor from ENTRY to EXIT as BFS."""
        queue: deque[tuple[int, int]] = deque([self.maze.m_entry])

        visited: set[tuple[int, int]] = {self.maze.m_entry}

        came_from: dict[tuple[int, int], tuple[int, int] | None] \
            = {self.maze.m_entry: None}

        directions = {
            (0, -1): Direction.NORTH,
            (1, 0): Direction.EAST,
            (0, 1): Direction.SOUTH,
            (-1, 0): Direction.WEST
        }

        moves = [
            (0, -1),
            (1, 0),
            (0, 1),
            (-1, 0)
        ]

        while queue and self.maze.m_exit not in visited:
            current: tuple[int, int] | None = queue.popleft()

            # if current == self.m_exit:
            #     path = []
            #     curr: tuple[int, int] | None = self.m_exit
            #
            #     while curr is not None:
            #         path.append(curr)
            #         curr = came_from[curr]
            #
            #     path.reverse()
            #     self.path = path
            #     print(path)
            #     break

            if current is not None:
                x, y = current
                cell_position = 1 << (y * self.maze.width + x)

                for wall_number, wall in enumerate(self.maze.get_walls()):

                    dx, dy = moves[wall_number]
                    nx = x + dx
                    ny = y + dy
                    if (
                            0 <= nx < self.maze.width
                            and 0 <= ny < self.maze.height
                            and (nx, ny) not in self.maze.locked_cells):
                        if not wall & cell_position:

                            if (nx, ny) not in visited:
                                visited.add((nx, ny))
                                came_from[(nx, ny)] = current
                                queue.append((nx, ny))
                                # TU
                                yield nx, ny, directions[(nx - x, ny - y)]
                                if (nx, ny) == self.maze.m_exit:
                                    path = []
                                    curr: tuple[int, int] | None \
                                        = self.maze.m_exit

                                    while curr is not None:
                                        path.append(curr)
                                        curr = came_from[curr]

                                    path.reverse()
                                    self.maze.path = path
                                    # print(path)
                                    break
