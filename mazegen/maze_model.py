# from __future__ import annotations
from enum import IntFlag

from mazegen.utils import get_pattern_locked_cells
from .utils import Direction
from typing import Generator
from collections import deque


class Wall(IntFlag):
    """
    Bitwise flags representing the walls of a single maze cell.
    """
    N = 1  # 0001
    E = 2  # 0010
    S = 4  # 0100
    W = 8  # 1000

    ALL = 1 | 2 | 4 | 8


class Maze:
    """
    Represents the maze grid.

    Attributes:
        width: The width of the maze.
        height: The height of the maze.
        perfect: Boolean indicating if the maze should be perfect (no loops).
        m_entry: A tuple representing the (x, y) coordinates of the start.
        m_exit: A tuple representing the (x, y) coordinates of the exit.
    """

    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            walls_n: int,
            walls_e: int,
            walls_s: int,
            walls_w: int,
            # seed: int | None,
            # output_file: str | None,
            # algorithm: str | None,
    ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect

        self.walls_n: int = walls_n
        self.walls_e: int = walls_e
        self.walls_s: int = walls_s
        self.walls_w: int = walls_w

        self.locked_cells = get_pattern_locked_cells(self.width, self.height)

        self.solver: str = 'dfs' # dfs or bfs, need to solve it in config !!!!!!!
        self.path: list[tuple[int, int]] = []
        if self.solver == 'dfs':
            self._animation_iterator = self.solver_dfs()
        else:
            self._animation_iterator = self.solver_bfs()


    def solve(self) -> list[str]:
        """mocked solve"""
        # TODO IMPLEMENT
        return ['E', 'S', 'E', 'N', 'E']

    def save_to_file(self, filepath: str) -> None:
        """Saves the maze to a file"""
        # TODO IMPLEMENT
        pass

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def step(self) -> tuple[int, int, Direction] | None:

        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    def solver_bfs(self) -> Generator[
        tuple[int, int, Direction], None, None]:
        """Find corridor from ENTRY to EXIT as BFS.
        """
        queue: deque[tuple[int, int]] = deque([self.m_entry])

        visited: set[tuple[int, int]] = {self.m_entry}

        came_from: dict[tuple[int, int], tuple[int, int] | None] \
            = {self.m_entry: None}

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

        while queue:
            current: tuple[int, int] | None = queue.popleft()

            if current == self.m_exit:
                path = []
                curr: tuple[int, int] | None = self.m_exit

                while curr is not None:
                    path.append(curr)
                    curr = came_from[curr]

                path.reverse()
                self.path = path
                print(path)
                break

            if current is not None:
                x, y = current
                cell_position = 1 << (y * self.width + x)

                for wall_number, wall in enumerate(self.get_walls()):

                    dx , dy = moves[wall_number]
                    nx = x + dx
                    ny = y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height
                            and (nx, ny) not in self.locked_cells):
                        if not wall & cell_position:

                            if (nx, ny) not in visited:
                                visited.add((nx, ny))
                                came_from[(nx, ny)] = current
                                queue.append((nx, ny))
                                # TU
                                yield nx, ny, directions[(nx - x, ny - y)]


    def solver_dfs(self) -> Generator[
        tuple[int, int, Direction], None, None]:
        """Find corridor from ENTRY to EXIT as BFS.
        """
        stack: list[tuple[int, int]] = [self.m_entry]

        visited: set[tuple[int, int]] = {self.m_entry}

        came_from: dict[tuple[int, int], tuple[int, int] | None] \
            = {self.m_entry: None}

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

        while stack:
            current: tuple[int, int] | None = stack.pop()

            if current == self.m_exit:
                path = []
                curr: tuple[int, int] | None = self.m_exit

                while curr is not None:
                    path.append(curr)
                    curr = came_from[curr]

                path.reverse()
                self.path = path
                print(path)
                break

            if current is not None:
                x, y = current
                cell_position = 1 << (y * self.width + x)

                for wall_number, wall in enumerate(self.get_walls()):

                    dx , dy = moves[wall_number]
                    nx = x + dx
                    ny = y + dy
                    if (0 <= nx < self.width and 0 <= ny < self.height
                            and (nx, ny) not in self.locked_cells):
                        if not wall & cell_position:

                            if (nx, ny) not in visited:
                                visited.add((nx, ny))
                                came_from[(nx, ny)] = current
                                stack.append((nx, ny))
                                # TU
                                yield nx, ny, directions[(nx - x, ny - y)]
