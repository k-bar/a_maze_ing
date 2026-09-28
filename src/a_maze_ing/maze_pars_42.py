from __future__ import annotations

import random
import sys
from typing import Literal
import typing
from enum import IntFlag
from .kruskal import UnionFind

try:
    from pydantic import BaseModel, Field, ValidationError, model_validator
except ImportError:
    print("------>      pip install pydantic")
    sys.exit(1)


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


class Config(BaseModel):
    """
    Pydantic model representing the configuration for the maze generator.

    Attributes:
        WIDTH (int): The width of the maze. Mandatory.
        HEIGHT (int): The height of the maze. Mandatory.
        ENTRY (tuple): Starting coordinates (x, y). Default is (0, 0).
        EXIT (tuple): Target coordinates (x, y). Default is (0, 0).
        OUTPUT_FILE (str | None): File path to save the output.
        PERFECT (bool): If True, generates a perfect maze without loops.
        SEED (str): Random seed used for generation reproducible results.
        ALGORITHM (str): The maze generation algorithm to use.
        ANIMATION (bool): If True, enables solving/generation animation.
        COLOR (str): Primary color for rendering.
        DISPLAY_MODE (str): Output mode (e.g., MLX or Terminal).
    """
    WIDTH: int = Field(..., ge=2, le=1000)
    HEIGHT: int = Field(..., ge=2, le=1000)
    ENTRY: tuple[int, int] = Field(default=(0, 0))
    EXIT: tuple[int, int] = Field(default=(0, 0))
    OUTPUT_FILE: str | None = Field(default=None, min_length=1, max_length=80)
    PERFECT: bool = Field(default=True)

    SEED: str = Field(default="42", min_length=1, max_length=80)

    ALGORITHM: Literal["KRUSKAL", "PRIM", "BACKTRACKER"] = (
        Field(default="KRUSKAL"))

    ANIMATION: bool = Field(default=True)
    COLOR: str = Field(default="green", min_length=1, max_length=80)
    DISPLAY_MODE: str = Field(default="MLX", min_length=1, max_length=80)

    @model_validator(mode='after')
    def validate_config(self) -> 'Config':
        """
        Validates the configuration parameters post-initialization.

        Ensures that the ENTRY and EXIT coordinates are within the
        boundaries defined by WIDTH and HEIGHT.

        Returns:
            Config: The validated Config instance.

        Raises:
            ValueError: If the entry or exit points are out of bounds.
        """

        def entry_exit(point: tuple[int, int], height: int,
                       width: int) -> bool:
            x, y = point
            if not (0 <= x < width) or not (0 <= y < height):
                raise ValueError(f"znajduje się poza planszą "
                                 f"{self.WIDTH}x{self.HEIGHT}!")
            else:
                return True

        try:
            entry_exit(self.ENTRY, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Punkt ENTRY {e}")

        try:
            entry_exit(self.EXIT, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Punkt EXIT {e}")

        return self


def read_config(name: str) -> Config | None:
    """
    Opens and reads a configuration file.

    Args:
        name: The path to the configuration file.

    Returns:
        Config | None: A validated Config instance, or exits the program
                       if a file reading error occurs.
    """
    try:
        with open(name, "r", encoding='utf-8') as f:
            return read_and_parse(f)
    except OSError as e:
        print(f"Błąd otwierania pliku '{name}': {e}")
        sys.exit(1)


def read_and_parse(file: typing.IO[str]) -> Config | None:
    """
    Parses the configuration content and converts it into a Config object.

    Expects lines in the format 'KEY = VALUE'. It ignores empty lines and
    comments starting with '#'. It specifically intercepts 'ENTRY' and 'EXIT'
    keys to cast their string values (e.g., "0,0") into tuples before passing
    them to the Pydantic model for validation.

    Args:
        file: An iterable text I/O stream containing the raw config data.

    Returns:
        Config | None: A fully instantiated Configuration object, or exits
                       the program upon validation failure or empty data.
    """
    config_data = {}

    for line in file:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue

        if "=" in clean_line:
            key, val = clean_line.split("=", 1)
            key, val = key.strip(), val.strip()

            if key in ["ENTRY", "EXIT"] and "," in val:
                try:
                    val = tuple(map(int, val.split(",")))
                except ValueError as e:
                    print(f"Punkt ENTRY/EXIT jest niepoprawny! \n {e}")
                    sys.exit(1)

            config_data[key] = val

    if config_data:
        try:
            config = Config(**config_data)
            print("Konfiguracja załadowana pomyślnie:\n")
            return config

        except ValidationError as e:
            print("Błąd walidacji pliku konfiguracyjnego:\n")
            print(e)
            sys.exit(1)
    else:
        print("Plik konfiguracyjny jest pusty lub nie ma "
              "danych w formacie KLUCZ=WARTOŚĆ.")
        sys.exit(1)