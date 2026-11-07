import random
from enum import IntFlag, auto

from .utils import get_pattern_locked_cells
from .utils import Direction


class Wall(IntFlag):
    """Bitwise flags representing the walls of a single maze cell."""
    N = auto()  # 1 = 0001
    E = auto()  # 2 = 0010
    S = auto()  # 4 = 0100
    W = auto()  # 8 = 1000

    ALL = N | E | S | W


class Maze:
    """Represents the maze grid.

    Attributes:
        width: The width of the maze.
        height: The height of the maze.
        perfect: Boolean indicating if the maze should be perfect (no loops).
        m_entry: A tuple representing the (x, y) coordinates of the start.
        m_exit: A tuple representing the (x, y) coordinates of the exit.
    """

    def __init__(self,
                 width: int,
                 height: int,
                 m_entry: tuple[int, int],
                 m_exit: tuple[int, int],
                 perfect: bool,
                 seed: int | None = None,
                 ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect
        self.seed = seed

        total_cells = width * height
        full_mask = (1 << total_cells) - 1

        self.walls_n: int = full_mask
        self.walls_e: int = full_mask
        self.walls_s: int = full_mask
        self.walls_w: int = full_mask

        self.locked_cells = get_pattern_locked_cells(self.width, self.height)
        self.locked_cells_mask: int = 0
        for x, y in self.locked_cells:
            self.locked_cells_mask |= (1 << y * self.width + x)

        self.path: list[tuple[int, int]] = []

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

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

    def pick_next_cell(self, cell: int, forbidden: int) -> int | None:

        moves = [d for d in Direction if
                 self.is_move_possible(cell, d, forbidden)]
        if not moves:
            return None
        picked_direction = random.choice(moves)
        return self.next_index(cell, picked_direction)

    def gather_possible_neighbours(self, cell: int, forbidden: int) \
            -> list[int | None]:
        moves = [d for d in Direction if
                 self.is_move_possible(cell, d, forbidden)]
        result = []
        for next_dir in moves:
            next_cell = self.next_index(cell, next_dir)
            result.append(next_cell)
        return result

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
        move_map = {
            Direction.NORTH: (self.is_north_border_cell, -self.width),
            Direction.EAST: (self.is_east_border_cell, 1),
            Direction.SOUTH: (self.is_south_border_cell, self.width),
            Direction.WEST: (self.is_west_border_cell, -1),
        }
        is_border, offset = move_map[picked_dir]

        if is_border(cell):
            return False

        next_cell = cell + offset
        return forbidden & (1 << next_cell) == 0

    def is_north_border_cell(self, index: int) -> bool:
        return index < self.width

    def is_south_border_cell(self, index: int) -> bool:
        return index >= self.width * (self.height - 1)

    def is_east_border_cell(self, index: int) -> bool:
        return (index + 1) % self.width == 0

    def is_west_border_cell(self, index: int) -> bool:
        return (index % self.width) == 0
