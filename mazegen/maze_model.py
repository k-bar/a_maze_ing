# from __future__ import annotations
from enum import IntFlag


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

    def step(self) -> tuple[int, int] | None:
        if self.generator is None:
            return None

        changed_cell = self.generator.step()
        if changed_cell is not None:
            return None

        self.walls_n, self.walls_e, self.walls_s, self.walls_w \
            = self.generator.get_walls()
        return changed_cell

    def _forty_two(self) -> None:
        """
        Blocks specific cells in the center of the grid to form a '42' shape.

        Algorithms building the maze must check `is_locked(x, y)` to avoid
        routing paths through these coordinates. If the maze dimensions are
        too small (width < 9 or height < 7) to enclose the pattern, it is
        aborted and a warning is printed.
        """
        pattern = [
            (-3, -2), (1, -2), (2, -2), (3, -2),
            (-3, -1), (3, -1),
            (-3, 0), (-2, 0), (-1, 0), (1, 0), (2, 0), (3, 0),
            (-1, 1), (1, 1),
            (-1, 2), (1, 2), (2, 2), (3, 2)
        ]

        if self.width < 9 or self.height < 7:
            print("Size of the MAZE is too small to include '42' pattern!")
            return

        cx = self.width // 2
        cy = self.height // 2

        for dx, dy in pattern:
            loc_x, loc_y = cx + dx, cy + dy
            self.locked_cells.add((loc_x, loc_y))
