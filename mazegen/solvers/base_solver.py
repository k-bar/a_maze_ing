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

    def _get_directions_map(self) -> tuple[tuple[Direction, int, int], ...]:
        maze_walls = self.maze.get_walls()
        border_mask = self.maze.border_masks
        width = self.maze.width

        return tuple(
            (
                d,
                maze_walls[d.bit_index] | border_mask[d.bit_index],
                d.get_flat_offset(width),
            )
            for d in Direction
        )

    def _reconstruct_path(
            self,
            came_from: dict[int, int],
            start_idx: int,
            exit_idx: int,
    ) -> None:
        width = self.maze.width
        indices = [exit_idx]
        curr = exit_idx

        while curr in came_from:
            curr = came_from[curr]
            indices.append(curr)

        self.maze.path = [
            (idx % width, idx // width) for idx in reversed(indices)
        ]
