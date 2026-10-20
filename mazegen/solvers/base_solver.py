from abc import ABC, abstractmethod
from typing import Generator

from ..maze_model import Maze
from ..utils import Direction


class MazeSolver(ABC):

    def __init__(self, maze: Maze) -> None:
        self.maze = maze
        self._animation_iterator = self._solve_loop()

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    @abstractmethod
    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        pass

    def solve_all(self) -> list[tuple[int, int]]:
        while self.step() is not None:
            pass
        return self.maze.path
