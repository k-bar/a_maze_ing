import random
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


class ImperfectGenerator(BaseGenerator):

    def __init__(self, base_generator: BaseGenerator) -> None:
        super().__init__(base_generator.maze)
        self.base_generator = base_generator

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """Remove walls from eligible dead-end cells.

        Scans the maze in row-major order. For each unlocked cell with
        exactly three walls, removes a randomly selected wall to an eligible
        neighboring cell, if one exists. The maze grid is modified in place.
        Random choices are initialized using the maze seed.
        """

        while (base_step := self.base_generator.step()) is not None:
            yield base_step

        if self.maze.perfect:
            return

        if self.maze.seed is not None:
            random.seed(self.maze.seed)
        visited: set[tuple[int, int]] = set()
        blind_ends: list[tuple[int, int]] = []

        for y in range(self.maze.height):
            for x in range(self.maze.width):
                if (x, y) not in self.maze.locked_cells:

                    cell_pos = 1 << ((y * self.maze.width) + x)

                    wall_count = 0
                    for wall in self.maze.get_walls():
                        if wall & cell_pos:
                            wall_count += 1

                    if wall_count == 3:
                        blind_ends.append((x, y))

        random.shuffle(blind_ends)

        while blind_ends:
            x, y = blind_ends.pop()
            cell_pos = 1 << ((y * self.maze.width) + x)
            wall_count = 0

            for wall in self.maze.get_walls():
                if wall & cell_pos:
                    wall_count += 1

            wn, we, ws, ww = self.maze.get_walls()
            if wall_count == 3:
                candidates = []

                if ((wn & cell_pos)
                        and y > 0
                        and (x, y - 1) not in (
                                self.maze.locked_cells | visited)):
                    candidates.append((x, y - 1))
                if ((we & cell_pos)
                        and x < self.maze.width - 1
                        and (x + 1, y) not in (self.maze.locked_cells
                                               | visited)):
                    candidates.append((x + 1, y))
                if ((ws & cell_pos)
                        and y < self.maze.height - 1
                        and (x, y + 1) not in (self.maze.locked_cells
                                               | visited)):
                    candidates.append((x, y + 1))
                if ((ww & cell_pos)
                        and x > 0
                        and (x - 1, y) not in (
                                self.maze.locked_cells | visited)):
                    candidates.append((x - 1, y))

                if candidates:
                    nx, ny = random.choice(candidates)

                    cell_a = cell_pos
                    cell_b = 1 << (
                            (ny * self.maze.width) + nx)

                    visited.add((x, y))

                    dx = nx - x
                    dy = ny - y

                    if dx > 0:
                        self.maze.walls_e &= ~cell_a
                        self.maze.walls_w &= ~cell_b
                        yield x, y, Direction.EAST
                    elif dx < 0:
                        self.maze.walls_w &= ~cell_a
                        self.maze.walls_e &= ~cell_b
                        yield x, y, Direction.WEST
                    elif dy > 0:
                        self.maze.walls_s &= ~cell_a
                        self.maze.walls_n &= ~cell_b
                        yield x, y, Direction.SOUTH
                    elif dy < 0:
                        self.maze.walls_n &= ~cell_a
                        self.maze.walls_s &= ~cell_b
                        yield x, y, Direction.NORTH
