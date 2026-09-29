from __future__ import annotations

import random
from app.config_parser import Config
from enum import IntFlag
from .kruskal import UnionFind




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
        entry: A tuple representing the (x, y) coordinates of the start.
        exit: A tuple representing the (x, y) coordinates of the exit.
        grid: A 2D list storing the Wall flags for each cell.
        locked_cells: A set of (x, y) coordinates blocked for the '42' pattern.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the Maze using the provided configuration.

        Args:
            config: A validated Config object containing maze parameters.
        """
        self.width = config.WIDTH
        self.height = config.HEIGHT
        self.perfect = config.PERFECT
        self.entry = config.ENTRY
        self.exit = config.EXIT

        self.grid: list[list[Wall]] = [
            [Wall.ALL for _ in range(self.width)] for _ in range(self.height)
        ]

        self.locked_cells = set()
        self._forty_two()

        if config.ALGORITHM == "KRUSKAL":
            self._prepare_kruskal()
            self._generate_kruskal(config.SEED)

    def display_unicode(self) -> None:
        """
        Draws the maze graphically in the terminal using Unicode characters.

        The canvas dimensions are expanded (2 characters per cell + 1 for the
        final wall). The entire canvas is initially filled with solid walls ('|').
        It then carves out empty spaces for the cells and the demolished walls
        using bitwise operations, skipping the locked '42' pattern cells.
        Finally, it marks the entry ('ST') and exit ('EX') points.
        """
        canvas_h = self.height * 2 + 1
        canvas_w = self.width * 2 + 1

        canvas = [['|' for _ in range(canvas_w)] for _ in range(canvas_h)]

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.locked_cells:
                    continue

                cy = y * 2 + 1
                cx = x * 2 + 1

                canvas[cy][cx] = ' '

                cell = self.grid[y][x]

                if (cell & Wall.N) == 0:
                    canvas[cy - 1][cx] = ' '
                if (cell & Wall.S) == 0:
                    canvas[cy + 1][cx] = ' '
                if (cell & Wall.W) == 0:
                    canvas[cy][cx - 1] = ' '
                if (cell & Wall.E) == 0:
                    canvas[cy][cx + 1] = ' '

                if (x, y) == self.entry:
                    canvas[cy][cx] = 'S'
                elif (x, y) == self.exit:
                    canvas[cy][cx] = 'E'

        for row in canvas:
            line = ""
            for char in row:
                if char == '|':
                    line += "||"
                elif char == ' ':
                    line += "  "
                elif char == 'S':
                    line += "ST"
                elif char == 'E':
                    line += "EX"
            print(line)

    def _prepare_kruskal(self) -> None:
        """
        Prepares the Union-Find data structure for Kruskal's algorithm.

        Adds every cell coordinates to the Union-Find structure as a separate
        set, skipping any coordinates belonging to the locked '42' pattern.
        """
        self.uf = UnionFind()

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.locked_cells:
                    self.uf.add((x, y))

    def _generate_kruskal(self, seed_val: str) -> None:
        """
        Generates the maze using a randomized Kruskal's algorithm.

        Collects all possible internal edges (West-East and North-South)
        excluding locked cells, shuffles them using the provided seed,
        and iterates through them. If an edge connects two disjoint sets,
        they are merged in the Union-Find structure and the dividing walls
        are demolished in the grid.

        Args:
            seed_val: A string seed used to initialize the random number
                      generator for reproducible maze layouts.
        """
        DIRECTION_MAP = {
            (1, 0): (Wall.E, Wall.W),
            (-1, 0): (Wall.W, Wall.E),
            (0, 1): (Wall.S, Wall.N),
            (0, -1): (Wall.N, Wall.S),
        }
        random.seed(seed_val)

        edges: list[tuple[int, int], tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.locked_cells:
                    continue

                if x + 1 < self.width and (x + 1, y) not in self.locked_cells:
                    edges.append(((x, y), (x + 1, y)))

                if y + 1 < self.height and (x, y + 1) not in self.locked_cells:
                    edges.append(((x, y), (x, y + 1)))

        random.shuffle(edges)

        for cell1, cell2 in edges:
            if self.uf.union(cell1, cell2):
                x1, y1 = cell1
                x2, y2 = cell2

                dx = x2 - x1
                dy = y2 - y1

                wall1, wall2 = DIRECTION_MAP[(dx, dy)]

                self.grid[y1][x1] &= ~wall1
                self.grid[y2][x2] &= ~wall2

    def is_locked(self, xy: tuple[int, int]) -> bool:
        """
        Checks if a given cell is part of the locked cells set.

        Args:
            xy: A tuple of (x, y) coordinates to check.

        Returns:
            bool: True if the cell is locked, False otherwise.
        """
        if xy in self.locked_cells:
            return True
        return False

    def display(self) -> None:
        """
        Prints the raw numerical values of the cells in the maze grid.
        """
        for row in self.grid:
            print(f"{[int(cell) for cell in row]}")

    def display_42(self) -> None:
        """
        Prints a stylized text representation of the maze cell values.

        Entry is marked with '[ ]', exit with '[.]', locked '42' pattern
        cells with '[_]', and regular cells with their hexadecimal wall value.
        """
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if (x, y) == self.entry:
                    print("[ ] ", end="")
                elif (x, y) == self.exit:
                    print("[.] ", end="")
                elif self.is_locked((x, y)):
                    print("[_] ", end="")
                else:
                    print(f"[{int(cell):X}] ", end="")
            print()

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
