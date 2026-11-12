from abc import ABC, abstractmethod
from typing import Generator

from ..maze_model import Maze
from ..utils import Direction


class MazeSolver(ABC):
    """Abstract base class for maze solving algorithms.

    Provides a framework for stepping through a maze solving algorithm
    (useful for animations) or solving the maze entirely at once. Subclasses
    must implement the `_solve_loop` method.

    Attributes:
        maze (Maze): The maze instance to be solved.
    """

    def __init__(self, maze: Maze) -> None:
        """Initializes the maze solver.

        Args:
            maze (Maze): The maze model that needs to be solved.
        """
        self.maze = maze
        self._animation_iterator = self._solve_loop()

    def step(self) -> tuple[int, int, Direction] | None:
        """Executes a single step of the solving algorithm.

        Useful for animating the solving process step-by-step.

        Returns:
            tuple[int, int, Direction] | None: A tuple containing the x and y
                coordinates and the direction of the current step, or None if
                the maze is completely solved.
        """
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    @abstractmethod
    def _solve_loop(self) -> Generator[tuple[int, int, Direction], None, None]:
        """Core solving algorithm loop.

        Subclasses must implement this method to define the specific
        pathfinding logic (e.g., BFS, DFS, A*). It should yield the current
        position and direction at each step of the search.

        Yields:
            tuple[int, int, Direction]: The x coordinate, y coordinate, and
                direction explored in the current step.
        """
        pass

    def solve_all(self) -> list[tuple[int, int]]:
        """Executes the entire solving algorithm without yielding.

        Exhausts the step generator to find the solution immediately.

        Returns:
            list[tuple[int, int]]: The final path from the start to the exit,
                represented as a list of (x, y) coordinate tuples.
        """
        while self.step() is not None:
            pass
        return self.maze.path

    def _get_directions_map(self) -> tuple[tuple[Direction, int, int], ...]:
        """Precomputes movement data for fast neighbor lookups.

        Combines wall bitmasks, border bitmasks, and flat 1D index offsets
        for all possible directions to optimize boundary and wall collision
        checks during the search.

        Returns:
            tuple[tuple[Direction, int, int], ...]: A tuple of configurations
                for each direction, containing the Direction enum, the combined
                wall/border mask, and the 1D array index offset.
        """
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
        """Reconstructs the final solution path by backtracking.

        Follows the chain of traversed nodes from the exit back to the start
        and updates the maze's `path` attribute with 2D coordinates.

        Args:
            came_from (dict[int, int]): A mapping of node indices to the index
                of the node they were reached from.
            start_idx (int): The 1D index of the starting position.
            exit_idx (int): The 1D index of the exit position.
        """
        width = self.maze.width
        indices = [exit_idx]
        curr = exit_idx

        while curr in came_from:
            curr = came_from[curr]
            indices.append(curr)

        self.maze.path = [
            (idx % width, idx // width) for idx in reversed(indices)
        ]
