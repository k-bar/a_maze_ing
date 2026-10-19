import random
from abc import ABC, abstractmethod

from mazegen.utils import Direction


class BaseGenerator(ABC):
    @abstractmethod
    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            seed: int | None = None
    ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect
        self.seed = seed

        # total_cells = width * height
        # full_mask = (1 << total_cells) - 1
        #
        self.walls_n: int
        self.walls_e: int
        self.walls_s: int
        self.walls_w: int

    @abstractmethod
    def step(self) -> tuple[int, int, Direction] | None:
        """
        Performs exactly one logic step of wall breaking

        Returns: (x, y, local_mas) of the cell that was changed,
        None when algorithm finished its work
        """
        pass

    def get_walls(self) -> tuple[int, int, int, int]:
        """Returns: 4 big logic bitmasks for walls of entire maze"""
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
