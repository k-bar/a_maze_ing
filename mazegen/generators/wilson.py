import random
from http.cookiejar import cut_port_re
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

    def destroy_both_walls(self, index: int, dir: Direction) -> None:
        n_index = self.next_index(index, dir)
        match dir:
            case Direction.NORTH:
                self.walls_n &= ~(1 << index)
                self.walls_s &= ~(1 << n_index)
            case Direction.EAST:
                self.walls_e &= ~(1 << index)
                self.walls_w &= ~(1 << n_index)
            case Direction.SOUTH:
                self.walls_s &= ~(1 << index)
                self.walls_n &= ~(1 << n_index)
            case Direction.WEST:
                self.walls_w &= ~(1 << index)
                self.walls_e &= ~(1 << n_index)

    def _algorithm_loop(self) -> Generator[
        tuple[int, int, Direction], None, None]:
        # TODO needed?
        random.seed(self.seed)

        ### steps ###

        # pick random cell A

        wn, we, ws, ww = self.get_walls()
        untouched_mask = wn & we & ws & ww

        # chosen_cell: int
        untouched_cells: list[int] = []
        for index in range(self.width * self.height):
            if untouched_mask & (1 << index):
                untouched_cells.append(index)

        print("u ", len(untouched_cells))

        maze_cells: list[int] = []
        first_maze_cell = untouched_cells.pop(
            random.randrange(len(untouched_cells)))
        maze_cells.append(first_maze_cell)

        while untouched_cells:
            print("u: ", len(untouched_cells))
            # for wall in self.get_walls():
            #     wall &= ~(1 << chosen_cell)
            #
            # x = chosen_cell // self.width
            # y = chosen_cell % self.height
            # untouched_cells.remove(chosen_cell)
            #
            # yield x, y, Direction.NORTH

            # pick another random cell B
            # exit?
            current_path: list[int] = []
            chosen_cell = untouched_cells.pop(
                random.randrange(len(untouched_cells)))
            while chosen_cell:
                current_path.append(chosen_cell)

                # if is_border_cell(chosen_cell)
                picked_dir = random.choice(list(Direction))
                while not is_move_possible(chosen_cell, self.width,
                                           self.height,
                                           picked_dir):
                    # print("tututut")
                    picked_dir = random.choice(list(Direction))

                new_cell = self.next_index(chosen_cell, picked_dir)

                if new_cell not in current_path:
                    current_path.append(new_cell)
                    self.destroy_both_walls(chosen_cell, picked_dir)
                    x, y = self.get_coords(chosen_cell)
                    yield x, y, picked_dir
                else:
                    cross_cell_index = current_path.index(new_cell)
                    while len(current_path) > cross_cell_index + 1:
                        popped_cell = current_path.pop()
                        previous_cell = current_path[len(current_path) - 1]
                        x, y = self.get_coords(popped_cell)
                        xp, yp = self.get_coords(previous_cell)
                        dx = xp - x
                        dy = yp - y
                        back_dir = Direction.from_xy(dx, dy)
                        # TODO WALL (from visited FLOOR)
                        yield x, y, back_dir

            # print("curcel", chosen_cell, "new cell", new_cell)

            #      0   1   2   3   4
            # 0  # 0   1   2   3   4
            #                  ^
            # 1  # 5   6   7   8   9
            #
            # 2  # 10  11  12  13  14
            #
            # 3  # 15> 16  17  18  19
            #      ^
            # 4  # 20  21  22  23  24

            # print(chosen_cell % self.width,
            #       chosen_cell // self.width,
            #       picked_dir)

            # take step from B in random direction towards cell C
            # destroying walls

            # choose randomly direction

            # repeat steps for C as for B

            # if broke back to already done corridor
            #   - erase the loop and continue from place when it crossed
            # if hit cell A, stop, take new cell


# def is_border_cell(index: int, width: int, height: int) -> bool:
#     return (is_north_border_cell(index, width)
#             or is_south_border_cell(index, width, height)
#             or is_east_border_cell(index, width, height)
#             or is_west_border_cell(index, width, height))


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

    # if (is_north_border_cell(index, width) and picked_dir == Direction.NORTH)
    #     or (is_east_border_cell(index, width) and picked_dir == Direction.EAST)


def is_north_border_cell(index: int, width: int) -> bool:
    return index < width


def is_south_border_cell(index: int, width: int, height: int) -> bool:
    return index >= width * (height - 1)


def is_east_border_cell(index: int, width: int) -> bool:
    return index % width == 0


def is_west_border_cell(index: int, width: int) -> bool:
    return (index % width) == 0
