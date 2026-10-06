# from __future__ import annotations
from enum import IntFlag

from mazegen.utils import get_pattern_locked_cells


class Wall(IntFlag):
    """
    Bitwise flags representing the walls of a single maze cell.
    """
    N = 1  # 0001
    E = 2  # 0010
    S = 4  # 0100
    W = 8  # 1000

    ALL = 1 | 2 | 4 | 8


class Maze:
    """
    Represents the maze grid.

    Attributes:
        width: The width of the maze.
        height: The height of the maze.
        perfect: Boolean indicating if the maze should be perfect (no loops).
        m_entry: A tuple representing the (x, y) coordinates of the start.
        m_exit: A tuple representing the (x, y) coordinates of the exit.
    """

    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            walls_n: int,
            walls_e: int,
            walls_s: int,
            walls_w: int,
            # seed: int | None,
            # output_file: str | None,
            # algorithm: str | None,
    ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect

        self.walls_n: int = walls_n
        self.walls_e: int = walls_e
        self.walls_s: int = walls_s
        self.walls_w: int = walls_w

        self.locked_cells = get_pattern_locked_cells(self.width, self.height)

    def solve(self) -> list[str]:
        """mocked solve"""
        # TODO IMPLEMENT
        return ['E', 'S', 'E', 'N', 'E']

    def save_to_file(self, filepath: str) -> None:
        """Saves the maze to a file"""
        # TODO IMPLEMENT
        pass

    # self.generator: BaseGenerator | None = None

    # self.grid: list[list[Wall]] = [
    #     [Wall.ALL for _ in range(self.width)] for _ in range(self.height)
    # ]

    # self.locked_cells: set[tuple[int, int]] = set()
    # self._forty_two()
    # self.path: list[tuple[int, int]] = []
    # self.output_file = output_file

    # if self.algorithm == "KRUSKAL":
    #     try:
    #         from mazegen.generators import generate_kruskal, UnionFind
    #     except ImportError as e:
    #         print(f"Error importing Kruskal's algorithm: {e}")
    #         return
    #     self.uf = UnionFind()
    #     generate_kruskal(self)

    # def attach_generator(self, algorithm_name: str, seed: int) -> None:
    #   self.generator = create_stepping_generator(algorithm_name, self.width,
    #                                                self.height, seed)
    #     self.walls_n, self.walls_e, self.walls_s, self.walls_w \
    #         = self.generator.get_walls()

    # def step(self) -> tuple[int, int] | None:
    #     if self.generator is None:
    #         return None
    #
    #     changed_cell = self.generator.step()
    #     if changed_cell is not None:
    #         return None
    #
    #     self.walls_n, self.walls_e, self.walls_s, self.walls_w \
    #         = self.generator.get_walls()
    #     return changed_cell
