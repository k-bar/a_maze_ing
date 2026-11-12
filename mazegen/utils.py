"""Module containing maze generation utilities, including direction handling
and pattern locking."""
import sys
from enum import Enum


class Direction(Enum):
    """Enumeration of cardinal directions for 2D grid movement.

    Each direction is defined by a tuple containing its string label,
    y-axis delta, x-axis delta, and a unique bit index.
    """
    NORTH = ("N", -1, 0, 0)
    EAST = ("E", 0, 1, 1)
    SOUTH = ("S", 1, 0, 2)
    WEST = ("W", 0, -1, 3)

    @property
    def label(self) -> str:
        """str: The single-character string label of the direction
        (e.g., 'N')."""
        return self.value[0]

    @property
    def dy(self) -> int:
        """int: The delta value on the Y-axis (-1, 0, or 1)."""
        return self.value[1]

    @property
    def dx(self) -> int:
        """int: The delta value on the X-axis (-1, 0, or 1)."""
        return self.value[2]

    @property
    def bit_index(self) -> int:
        """int: A unique integer representing the bit index (0 to 3)."""
        return self.value[3]

    @classmethod
    def from_xy(cls, dx: int, dy: int) -> "Direction":
        """Retrieves the Direction corresponding to the given x and y deltas.

        Args:
            dx (int): The delta movement on the X-axis.
            dy (int): The delta movement on the Y-axis.

        Returns:
            Direction: The corresponding direction enumeration.

        Raises:
            ValueError: If no direction matches the provided dx and dy deltas.
        """
        try:
            return next(d for d in cls if d.dx == dx and d.dy == dy)
        except StopIteration as exc:
            raise ValueError(f"No Direction for dx={dx}, dy={dy}") from exc

    def get_flat_offset(self, width: int) -> int:
        """Calculates the 1D array offset for this direction in a 2D grid.

        Args:
            width (int): The width (number of columns) of the 2D grid.

        Returns:
            int: The linear offset corresponding to a movement in this
            direction.
        """
        return (width * self.dy) + self.dx


def get_pattern_locked_cells(width: int, height: int) -> set[tuple[int, int]]:
    """Blocks specific cells in the center of the grid to form a '42' shape.

    Algorithms building the maze must check if a cell is locked to avoid
    routing paths through these coordinates. If the maze dimensions are
    too small (width < 9 or height < 7) to enclose the pattern, the injection
    is aborted and a warning is printed to stderr.

    Args:
        width (int): The total width of the maze grid.
        height (int): The total height of the maze grid.

    Returns:
        set[tuple[int, int]]: A set of locked cell coordinates as (x, y)
        tuples.
    """
    coords: set[tuple[int, int]] = set()

    if width < 9 or height < 7:
        print("Size of the MAZE is too small to include '42' pattern!",
              file=sys.stderr)
        return coords

    pattern = [
        "#   ###",
        "#     #",
        "### ###",
        "  # #  ",
        "  # ###"
    ]

    start_x = (width - len(pattern[0])) // 2
    start_y = (height - len(pattern)) // 2

    for row_idx, line in enumerate(pattern):
        for col_idx, char in enumerate(line):
            if char == '#':
                coords.add((start_x + col_idx, start_y + row_idx))

    return coords
