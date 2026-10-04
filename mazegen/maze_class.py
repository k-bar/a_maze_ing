from __future__ import annotations
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
    Represents the maze grid and handles its generation and display.

    Attributes:
        width: The width of the maze.
        height: The height of the maze.
        perfect: Boolean indicating if the maze should be perfect (no loops).
        m_entry: A tuple representing the (x, y) coordinates of the start.
        exit: A tuple representing the (x, y) coordinates of the exit.
        grid: A 2D list storing the Wall flags for each cell.
        locked_cells: A set of (x, y) coordinates blocked for the '42' pattern.
    """

    def __init__(self, width: int,
                 height: int,
                 perfect: bool,
                 m_entry: tuple[int, int],
                 m_exit: tuple[int, int],
                 seed: int | None,
                 output_file: str | None,
                 algorithm: str | None,
                 ) -> None:
        """
        Initializes the Maze using the provided configuration.

        Args:
            config: A validated Config object containing maze parameters.
        """
        self.width = width
        self.height = height
        self.perfect = perfect
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.seed = seed
        self.algorithm = algorithm

        self.grid: list[list[Wall]] = [
            [Wall.ALL for _ in range(self.width)] for _ in range(self.height)
        ]

        self.locked_cells: set[tuple[int, int]] = set()
        self._forty_two()
        self.path: list[tuple[int, int]] = []
        self.output_file = output_file

        if self.algorithm == "KRUSKAL":
            try:
                from mazegen.generators import generate_kruskal, UnionFind
            except ImportError as e:
                print(f"Error importing Kruskal's algorithm: {e}")
                return
            self.uf = UnionFind()
            generate_kruskal(self)

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
