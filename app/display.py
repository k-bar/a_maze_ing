from mazegen.maze_class import Maze, Wall

# Colors for terminal output
CZERWONY = "\033[31m"
ZIELONY = "\033[32m"
ZOLTY = "\033[33m"
NIEBIESKI = "\033[34m"
RESET = "\033[0m"  # Resets the terminal color to default


def display_solved(maze: 'Maze', path: list[tuple[int, int]]) -> None:
    """Prints maze with solved path. """
    path_set = set(path)

    for y, row in enumerate(maze.grid):
        for x, cell in enumerate(row):
            if (x, y) in path_set:
                if (x, y) == maze.m_exit:
                    print(f"{CZERWONY}[.] {RESET}", end="")
                elif (x, y) == maze.m_entry:
                    print(f"{CZERWONY}['] {RESET}", end="")
                else:
                    print(f"{ZIELONY}[{int(cell):X}]{RESET} ", end="")
            elif (x, y) not in maze.locked_cells:
                print(f"[{int(cell):X}] ", end="")
            else:
                print(f"{NIEBIESKI}[_] {RESET}", end="")
        print()


def display_solved_labyrinth(maze: 'Maze',
                             path: list[tuple[int, int]]) -> None:
    """Prints solved maze with path, nicer look"""
    path_set: set[tuple[int, int]] = set(path)

    if not maze.grid:
        return

    width = len(maze.grid[0])

    EAST_MASK = 2
    SOUTH_MASK = 4

    print("+" + "---+" * width)

    for y, row in enumerate(maze.grid):
        print("|", end="")

        for x, cell in enumerate(row):
            if (x, y) in maze.locked_cells:
                content = f"{NIEBIESKI}[=]{RESET}"
            elif (x, y) in path_set:
                if (x, y) == maze.m_exit:
                    content = f"{CZERWONY}EXT{RESET}"
                elif (x, y) == maze.m_entry:
                    content = f"{CZERWONY}ENT{RESET}"
                else:
                    content = f"{CZERWONY} 0 {RESET}"
            else:
                content = "   "

            print(content, end="")

            if int(cell) & EAST_MASK:
                print("|", end="")
            else:
                print(" ", end="")

        print()

        print("+", end="")
        for x, cell in enumerate(row):
            if int(cell) & SOUTH_MASK:
                print("---+", end="")
            else:
                print("   +", end="")

        print()


def is_locked(maze: 'Maze', xy: tuple[int, int]) -> bool:
    """
    Checks if a given cell is part of the locked cells set.

    Args:
        xy: A tuple of (x, y) coordinates to check.

    Returns:
        bool: True if the cell is locked, False otherwise.
    """
    if xy in maze.locked_cells:
        return True
    return False


def display(maze: 'Maze') -> None:
    """
    Prints the raw numerical values of the cells in the maze grid.
    """
    for row in maze.grid:
        print(f"{[int(cell) for cell in row]}")


def display_42(maze: 'Maze') -> None:
    """
    Prints a stylized text representation of the maze cell values.

    Entry is marked with '[ ]', exit with '[.]', locked '42' pattern
    cells with '[_]', and regular cells with their hexadecimal wall value.
    """
    for y, row in enumerate(maze.grid):
        for x, cell in enumerate(row):
            if (x, y) == maze.m_entry:
                print("[ ] ", end="")
            elif (x, y) == maze.m_exit:
                print("[.] ", end="")
            elif is_locked(maze, (x, y)):
                print("[_] ", end="")
            else:
                print(f"[{int(cell):X}] ", end="")
        print()


def display_unicode(maze: 'Maze') -> None:
    """
    Draws the maze graphically in the terminal using Unicode characters.

    The canvas dimensions are expanded (2 characters per cell + 1 for the
    final wall). The entire canvas is initially filled with solid walls
    ('|').
    It then carves out empty spaces for the cells and the demolished walls
    using bitwise operations, skipping the locked '42' pattern cells.
    Finally, it marks the entry ('ST') and exit ('EX') points.
    """
    canvas_h = maze.height * 2 + 1
    canvas_w = maze.width * 2 + 1

    canvas = [['█' for _ in range(canvas_w)] for _ in range(canvas_h)]

    for y in range(maze.height):
        for x in range(maze.width):
            if (x, y) in maze.locked_cells:
                continue

            cy = y * 2 + 1
            cx = x * 2 + 1

            canvas[cy][cx] = ' '

            cell = maze.grid[y][x]

            if (cell & Wall.N) == 0:
                canvas[cy - 1][cx] = ' '
            if (cell & Wall.S) == 0:
                canvas[cy + 1][cx] = ' '
            if (cell & Wall.W) == 0:
                canvas[cy][cx - 1] = ' '
            if (cell & Wall.E) == 0:
                canvas[cy][cx + 1] = ' '

            if (x, y) == maze.m_entry:
                canvas[cy][cx] = 'S'
            elif (x, y) == maze.m_exit:
                canvas[cy][cx] = 'E'

    for row in canvas:
        line = ""
        for char in row:
            if char == '█':
                line += "██"
            elif char == ' ':
                line += "  "
            elif char == 'S':
                line += "ST"
            elif char == 'E':
                line += "EX"
        print(line)
