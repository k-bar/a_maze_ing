import random
from abc import abstractmethod, ABC
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


class Maze(ABC):
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
            solver: str,
            seed: int | None = None,
    ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect
        self.seed = seed

        self.walls_n: int
        self.walls_e: int
        self.walls_s: int
        self.walls_w: int

        self.locked_cells = get_pattern_locked_cells(self.width, self.height)

        self.solver: str = solver
        self.path: list[tuple[int, int]] = []

        if self.solver == 'DFS':
            self._path_animation_iterator = self.solver_dfs()
        else:
            self._path_animation_iterator = self.solver_bfs()

    @abstractmethod
    def step(self) -> tuple[int, int, Direction] | None:
        """
        Performs exactly one logic step of wall breaking

        Returns: (x, y, local_mas) of the cell that was changed,
        None when algorithm finished its work
        """
        pass

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def generate_all(self) -> None:
        """Performs whole algorithm at once"""
        while self.step() is not None:
            pass

    def flip_both_walls(self, cell: int, next_cell: int) -> None:
        _, _, direction = self.get_coords_and_dir(cell, next_cell)
        match direction:
            case Direction.NORTH:
                self.walls_n ^= (1 << cell)
                self.walls_s ^= (1 << next_cell)
            case Direction.EAST:
                self.walls_e ^= (1 << cell)
                self.walls_w ^= (1 << next_cell)
            case Direction.SOUTH:
                self.walls_s ^= (1 << cell)
                self.walls_n ^= (1 << next_cell)
            case Direction.WEST:
                self.walls_w ^= (1 << cell)
                self.walls_e ^= (1 << next_cell)

    def next_index(self, index: int, direction: Direction) -> int:
        return index + (self.width * direction.dy) + direction.dx

    def pick_possible_direction(self, cell: int, forbidden: int) -> Direction:
        picked_direction = random.choice(list(Direction))
        while not self.is_move_possible(cell, picked_direction, forbidden):
            picked_direction = random.choice(list(Direction))
        return picked_direction

    @staticmethod
    def pick_random_cell(mask: int, max_cells: int) -> int | None:
        if mask == 0:
            return None
        while True:
            candidate = random.randrange(max_cells)
            if mask & (1 << candidate):
                return candidate

    def get_coords(self, index: int) -> tuple[int, int]:
        return index % self.width, index // self.width

    def get_coords_and_dir(self, cell: int, next_cell: int) \
            -> tuple[int, int, Direction]:
        x, y = self.get_coords(cell)
        x_n, y_n = self.get_coords(next_cell)
        dx = x_n - x
        dy = y_n - y
        direction = Direction.from_xy(dx, dy)
        return x, y, direction

    def is_move_possible(self, cell: int, picked_dir: Direction,
                         forbidden: int) -> bool:
        match picked_dir:
            case Direction.NORTH:
                if self.is_north_border_cell(cell):
                    return False
                else:
                    next_cell = cell - self.width
                    return forbidden & (1 << next_cell) == 0
            case Direction.EAST:
                if self.is_east_border_cell(cell):
                    return False
                else:
                    next_cell = cell + 1
                    return forbidden & (1 << next_cell) == 0
            case Direction.SOUTH:
                if self.is_south_border_cell(cell):
                    return False
                else:
                    next_cell = cell + self.width
                    return forbidden & (1 << next_cell) == 0
            case Direction.WEST:
                if self.is_west_border_cell(cell):
                    return False
                else:
                    next_cell = cell - 1
                    return forbidden & (1 << next_cell) == 0

    def is_north_border_cell(self, index: int) -> bool:
        return index < self.width

    def is_south_border_cell(self, index: int) -> bool:
        return index >= self.width * (self.height - 1)

    def is_east_border_cell(self, index: int) -> bool:
        return (index + 1) % self.width == 0

    def is_west_border_cell(self, index: int) -> bool:
        return (index % self.width) == 0

    def path_step(self) -> tuple[int, int, Direction] | None:

        try:
            return next(self._path_animation_iterator)
        except StopIteration:
            return None

    def solver_bfs(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Find corridor from ENTRY to EXIT as BFS."""
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

        while queue and self.m_exit not in visited:
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
                cell_position = 1 << (y * self.width + x)

                for wall_number, wall in enumerate(self.get_walls()):

                    dx, dy = moves[wall_number]
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
                                if (nx, ny) == self.m_exit:
                                    path = []
                                    curr: tuple[int, int] | None = self.m_exit

                                    while curr is not None:
                                        path.append(curr)
                                        curr = came_from[curr]

                                    path.reverse()
                                    self.path = path
                                    # print(path)
                                    break

    def solver_dfs(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Find corridor from ENTRY to EXIT as BFS."""
        stack: list[tuple[int, int]] = ([self.m_entry])

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

        while stack and self.m_exit not in visited:
            current: tuple[int, int] | None = stack.pop()

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
                cell_position = 1 << (y * self.width + x)

                for wall_number, wall in enumerate(self.get_walls()):

                    dx, dy = moves[wall_number]
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
                                if (nx, ny) == self.m_exit:
                                    path = []
                                    curr: tuple[int, int] | None = self.m_exit

                                    while curr is not None:
                                        path.append(curr)
                                        curr = came_from[curr]

                                    path.reverse()
                                    self.path = path
                                    # print(path)
                                    break
