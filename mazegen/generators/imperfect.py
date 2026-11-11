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

        yield from self.make_imperfect()

    def generate_all(self) -> None:
        for _ in self.make_imperfect():
            pass

    @staticmethod
    def _count_walls(cell_pos: int,
                     walls: tuple[int, int, int, int]) -> int:
        return sum(bool(wall & cell_pos) for wall in walls)

    def make_imperfect(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """Remove walls from eligible dead-end cells.

        Scans the maze in row-major order. For each unlocked cell with
        exactly three walls, removes a randomly selected wall to an eligible
        neighboring cell, if one exists. The maze grid is modified in place.
        Random choices are initialized using the maze seed.
        """
        if self.maze.perfect:
            return

        if self.maze.seed is not None:
            random.seed(self.maze.seed)

        visited: set[tuple[int, int]] = set()
        blind_ends: list[tuple[int, int]] = []
        locked = set(self.maze.locked_cells)
        width = self.maze.width
        height = self.maze.height

        walls = self.maze.get_walls()
        for y in range(height):
            for x in range(width):
                if (x, y) not in locked:
                    cell_pos = 1 << ((y * width) + x)
                    if self._count_walls(cell_pos, walls) == 3:
                        blind_ends.append((x, y))

        random.shuffle(blind_ends)

        while blind_ends:
            x, y = blind_ends.pop()
            cell_pos = 1 << ((y * width) + x)
            wn, we, ws, ww = self.maze.get_walls()
            if self._count_walls(cell_pos, (wn, we, ws, ww)) == 3:
                candidates = []

                if ((wn & cell_pos) and y > 0
                        and (x, y - 1) not in locked
                        and (x, y - 1) not in visited):
                    candidates.append((x, y - 1))
                if ((we & cell_pos) and x < width - 1
                        and (x + 1, y) not in locked
                        and (x + 1, y) not in visited):
                    candidates.append((x + 1, y))
                if ((ws & cell_pos) and y < height - 1
                        and (x, y + 1) not in locked
                        and (x, y + 1) not in visited):
                    candidates.append((x, y + 1))
                if ((ww & cell_pos) and x > 0
                        and (x - 1, y) not in locked
                        and (x - 1, y) not in visited):
                    candidates.append((x - 1, y))

                if candidates:
                    nx, ny = random.choice(candidates)
                    visited.add((x, y))

                    cell_a_idx = (y * width) + x
                    cell_b_idx = (ny * width) + nx

                    self.maze.flip_both_walls(cell_a_idx, cell_b_idx)
                    yield self.maze.get_coords_and_dir(cell_a_idx, cell_b_idx)
