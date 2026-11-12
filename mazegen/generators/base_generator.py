import random
from abc import ABC, abstractmethod
from typing import Generator

from ..maze_model import Maze
from ..utils import Direction


class BaseGenerator(ABC):
    """
    Abstract base class for maze generation algorithms.

    Provides the core execution loop and state management for both
    step-by-step (animated) and instant maze generation.
    """
    def __init__(self, maze: Maze) -> None:
        """
        Initializes the base generator.

        Args:
            maze (Maze): The maze model instance to be generated.
        """
        self.maze = maze
        self._animation_iterator = self._algorithm_loop()

    def step(self) -> tuple[int, int, Direction] | None:
        """
        Performs exactly one logic step of wall breaking.

        Returns:
            tuple[int, int, Direction] | None: A tuple containing the (x, y)
            coordinates of the modified cell and the direction towards the
            next connected cell. Returns None when the algorithm has finished.
        """
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    @abstractmethod
    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """
        Abstract generator method defining the core algorithm loop.

        Must be implemented by subclasses to yield the sequence of
        wall-breaking operations.

        Yields:
            tuple[int, int, Direction]: The (x, y) coordinates and direction
            for each modified cell during generation.
        """
        pass

    def generate_all(self) -> None:
        """
        Executes the entire maze generation algorithm at once.

        Repeatedly advances the algorithm until all reachable cells are
        processed.
        """
        while self.step() is not None:
            pass

    def _initialize_generator(self) -> tuple[int, int, int]:
        """
        Sets up the initial state and bitmasks for the generation algorithm.

        Seeds the random number generator (if configured) and determines the
        starting cell, ignoring any pre-locked cells.

        Returns:
            tuple[int, int, int]: A tuple containing:
                - untouched_cells (int): A bitmask representing all unvisited
                  and unlocked cells.
                - first_maze_cell (int): The 1D index of the randomly chosen
                  starting cell.
                - max_cells (int): The total number of cells in the maze grid.
        """
        if self.maze.seed is not None:
            random.seed(self.maze.seed)

        max_cells = self.maze.width * self.maze.height
        untouched_cells = (1 << max_cells) - 1
        untouched_cells &= ~self.maze.locked_cells_mask
        first_maze_cell = self.maze.pick_random_cell(untouched_cells,
                                                     max_cells)
        untouched_cells &= ~(1 << first_maze_cell)

        return untouched_cells, first_maze_cell, max_cells
