import random
from abc import ABC, abstractmethod
from typing import Generator

from ..maze_model import Maze
from ..utils import Direction


class BaseGenerator(ABC):
    def __init__(self, maze: Maze) -> None:
        self.maze = maze
        self._animation_iterator = self._algorithm_loop()

    def step(self) -> tuple[int, int, Direction] | None:
        """
        Performs exactly one logic step of wall breaking

        Returns: (x, y, direction) of one the cell that was changed,
        and direction towards next that was also changed
        None when algorithm finished its work
        """
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    @abstractmethod
    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        pass

    def generate_all(self) -> None:
        """Performs whole algorithm at once"""
        while self.step() is not None:
            pass

    def _initialize_generator(self) -> tuple[int, int, int]:
        if self.maze.seed is not None:
            random.seed(self.maze.seed)

        max_cells = self.maze.width * self.maze.height
        untouched_cells = (1 << max_cells) - 1
        untouched_cells &= ~self.maze.locked_cells_mask
        first_maze_cell = self.maze.pick_random_cell(untouched_cells,
                                                     max_cells)
        untouched_cells &= ~(1 << first_maze_cell)

        return untouched_cells, first_maze_cell, max_cells
