import random
from typing import Generator

from mazegen.base import BaseGenerator


class MazeGenerator(BaseGenerator):
    """Temporary mock of generator using yield"""

    def __init__(self, width: int, height: int,
                 seed: int | None = None) -> None:
        self.width = width
        self.height = height
        if seed is not None:
            random.seed(seed)

        total_cells = width * height
        full_mask = (1 << total_cells) - 1

        self.walls_n: int = full_mask
        self.walls_e: int = full_mask
        self.walls_s: int = full_mask
        self.walls_w: int = full_mask

        self.animation_iterator: Generator[
            tuple[int, int, int], None, None] = self._algorithm_loop()

    def _algorithm_loop(self) -> Generator[tuple[int, int, int], None, None]:
        """simulation fo destroying walls step by step"""

        for y in range(self.height):
            for x in range(self.width):
                cell_index = (y * self.width) + x

                if random.choice([True, False]):
                    self.walls_n &= ~(1 << cell_index)
                if random.choice([True, False]):
                    self.walls_e &= ~(1 << cell_index)
                if random.choice([True, False]):
                    self.walls_s &= ~(1 << cell_index)
                if random.choice([True, False]):
                    self.walls_w &= ~(1 << cell_index)
                yield x, y,

    def step(self) -> tuple[int, int, int] | None:
        try:
            return next(self.animation_iterator)
        except StopIteration:
            return None

    def generate_all(self) -> None:
        while self.step() is not None:
            pass

    def generate_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def solve(self) -> list[str]:
        return ["E", "S", "E", "N", "E"]
