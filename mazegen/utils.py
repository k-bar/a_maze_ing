from enum import Enum


class Direction(Enum):
    NORTH = ("N", -1, 0, 0)
    EAST = ("E", 0, 1, 1)
    SOUTH = ("S", 1, 0, 2)
    WEST = ("W", 0, -1, 3)

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def dx(self) -> int:
        return self.value[2]

    @property
    def bit_index(self) -> int:
        return self.value[3]


def get_pattern_locked_cells(width: int, height: int) -> set[tuple[int, int]]:
    """
    Blocks specific cells in the center of the grid to form a '42' shape.

    Algorithms building the maze must check `is_locked(x, y)` to avoid
    routing paths through these coordinates. If the maze dimensions are
    too small (width < 9 or height < 7) to enclose the pattern, it is
    aborted and a warning is printed.

    Return: set of locked cells  as tuples of x, y coords
    """
    coords: set[tuple[int, int]] = set()

    if width < 9 or height < 7:
        print("Size of the MAZE is too small to include '42' pattern!")
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
