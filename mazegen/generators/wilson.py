import random
from typing import Generator

from mazegen import BaseGenerator
from mazegen.utils import Direction


class WilsonGenerator(BaseGenerator):
    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            seed: int | None = None
    ) -> None:
        super().__init__(width, height, m_entry, m_exit, perfect, seed)

        if seed is None:
            random.seed(seed)

        total_cells = width * height
        full_mask = (1 << total_cells) - 1

        self.walls_n: int = full_mask
        self.walls_e: int = full_mask
        self.walls_s: int = full_mask
        self.walls_w: int = full_mask

        self._animation_iterator: Generator[
            tuple[int, int, Direction], None, None] = self._algorithm_loop()

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    # TODO move to BaseGenerator

    def next_index(self, index: int, dir: Direction) -> int:
        return index + (self.width * dir.dy) + dir.dx

    def get_coords(self, index: int) -> tuple[int, int]:
        return index % self.width, index // self.width

    def flip_both_walls(self, cell: int, next_cell: int) -> None:
        _, _, direction = self.get_coords_and_dir(cell, next_cell)
        match direction:
            case Direction.NORTH:
                self.walls_n &= ~(1 << cell)
                self.walls_s &= ~(1 << next_cell)
            case Direction.EAST:
                self.walls_e &= ~(1 << cell)
                self.walls_w &= ~(1 << next_cell)
            case Direction.SOUTH:
                self.walls_s &= ~(1 << cell)
                self.walls_n &= ~(1 << next_cell)
            case Direction.WEST:
                self.walls_w &= ~(1 << cell)
                self.walls_e &= ~(1 << next_cell)

    def get_coords_and_dir(self, cell: int, next_cell: int) -> tuple[int, int, Direction]:
        x, y = self.get_coords(cell)
        xp, yp = self.get_coords(next_cell)
        dx = xp - x
        dy = yp - y
        direction = Direction.from_xy(dx, dy)
        return x, y, direction

    def pick_possible_direction(self, cell: int) -> Direction:
        picked_direction = random.choice(list(Direction))
        while not is_move_possible(cell, self.width,
                                   self.height,
                                   picked_direction):
            picked_direction = random.choice(list(Direction))
        return picked_direction

    def _algorithm_loop(self) -> Generator[
        tuple[int, int, Direction], None, None]:
        # TODO needed?
        random.seed(self.seed)

        max_cells = self.width * self.height
        untouched_cells = (1 << max_cells) - 1

        first_maze_cell = random.randrange(max_cells)
        untouched_cells &= ~(1 << first_maze_cell)

        while untouched_cells:

            start_cell = pick_random_cell(untouched_cells, max_cells)

            current_path = [start_cell]
            current_path_mask = 1 << start_cell

            while True:
                current_cell = current_path[-1]
                if current_cell is None:
                    break

                next_cell = self.next_index(current_cell,
                                            self.pick_possible_direction(current_cell))

                if not untouched_cells & (1 << next_cell):
                    self.flip_both_walls(current_cell, next_cell)
                    yield self.get_coords_and_dir(current_cell, next_cell)
                    while current_path:
                        cell = current_path.pop()
                        untouched_cells &= ~(1 << cell)
                    break

                elif current_path_mask & (1 << next_cell):

                    while current_path[-1] != next_cell:
                        removed = current_path.pop()
                        current_path_mask &= ~(1 << removed)
                        previous_cell = current_path[-1]
                        if removed is not None and previous_cell is not None:
                            self.flip_both_walls(removed, previous_cell)
                            yield self.get_coords_and_dir(removed, previous_cell)

                else:
                    current_path.append(next_cell)
                    current_path_mask |= (1 << next_cell)
                    self.flip_both_walls(current_cell, next_cell)
                    yield self.get_coords_and_dir(current_cell, next_cell)


def is_move_possible(index: int, width, height, picked_dir: Direction) -> bool:
    match picked_dir:
        case Direction.NORTH:
            return not is_north_border_cell(index, width)
        case Direction.EAST:
            return not is_east_border_cell(index, width)
        case Direction.SOUTH:
            return not is_south_border_cell(index, width, height)
        case Direction.WEST:
            return not is_west_border_cell(index, width)

    # TODO add locked cells


def is_north_border_cell(index: int, width: int) -> bool:
    return index < width


def is_south_border_cell(index: int, width: int, height: int) -> bool:
    return index >= width * (height - 1)


def is_east_border_cell(index: int, width: int) -> bool:
    return (index + 1) % width == 0


def is_west_border_cell(index: int, width: int) -> bool:
    return (index % width) == 0


def pick_random_cell(mask: int, max_cells: int) -> int | None:
    if mask == 0:
        return None

    while True:
        candidate = random.randrange(max_cells)
        if mask & (1 << candidate):
            return candidate
