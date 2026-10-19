import random
from typing import Generator

from .. import BaseGenerator
from ..utils import Direction, get_pattern_locked_cells


class ImperfectGenerator(BaseGenerator):

    def __init__(self, base_generator: BaseGenerator) -> None:
        super().__init__(
            width=base_generator.width,
            height=base_generator.height,
            m_entry=base_generator.m_entry,
            m_exit=base_generator.m_exit,
            perfect=False,
            seed=base_generator.seed
        )

        self.base_generator = base_generator
        self.locked_cells = (
            get_pattern_locked_cells(self.base_generator.width,
                                     self.base_generator.height))

        self._animation_iterator = self.del_death_ends()

    def step(self) -> tuple[int, int, Direction] | None:

        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    def del_death_ends(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """Remove walls from eligible dead-end cells.

        Scans the maze in row-major order. For each unlocked cell with
        exactly three walls, removes a randomly selected wall to an eligible
        neighboring cell, if one exists. The maze grid is modified in place.
        Random choices are initialized using the maze seed.

        Args:
            maze: Maze whose dead ends should be opened.
        """

        while (base_step := self.base_generator.step()) is not None:
            yield base_step

        if self.base_generator.seed is not None:
            random.seed(self.base_generator.seed)
        visited: set[tuple[int, int]] = set()

        for y in range(self.base_generator.height):
            for x in range(self.base_generator.width):
                if (x, y) not in self.locked_cells:

                    cell_pos = 1 << ((y * self.base_generator.width) + x)

                    wall_count = 0
                    for wall in self.base_generator.get_walls():
                        if wall & cell_pos:
                            wall_count += 1

                    wn, we, ws, ww = self.base_generator.get_walls()

                    if wall_count == 3:
                        candidates = []
                        if ((wn & cell_pos)
                                and y > 0
                                and (x, y - 1) not in (
                                        self.locked_cells | visited)):
                            candidates.append((x, y - 1))
                        if ((we & cell_pos)
                                and x < self.base_generator.width - 1
                                and (x + 1, y) not in (self.locked_cells
                                                       | visited)):
                            candidates.append((x + 1, y))
                        if ((ws & cell_pos)
                                and y < self.base_generator.height - 1
                                and (x, y + 1) not in (self.locked_cells
                                                       | visited)):
                            candidates.append((x, y + 1))
                        if ((ww & cell_pos)
                                and x > 0
                                and (x - 1, y) not in (
                                        self.locked_cells | visited)):
                            candidates.append((x - 1, y))

                        if candidates:
                            nx, ny = random.choice(candidates)

                            cell_a = cell_pos
                            cell_b = 1 << (
                                    (ny * self.base_generator.width) + nx)

                            visited.add((x, y))

                            dx = nx - x
                            dy = ny - y

                            if dx > 0:
                                self.base_generator.walls_e &= ~cell_a
                                self.base_generator.walls_w &= ~cell_b
                                yield x, y, Direction.EAST
                            elif dx < 0:
                                self.base_generator.walls_w &= ~cell_a
                                self.base_generator.walls_e &= ~cell_b
                                yield x, y, Direction.WEST
                            elif dy > 0:
                                self.base_generator.walls_s &= ~cell_a
                                self.base_generator.walls_n &= ~cell_b
                                yield x, y, Direction.SOUTH
                            elif dy < 0:
                                self.base_generator.walls_n &= ~cell_a
                                self.base_generator.walls_s &= ~cell_b
                                yield x, y, Direction.NORTH
