# Definiowanie kodów kolorów
CZERWONY = "\033[31m"
ZIELONY = "\033[32m"
ZOLTY = "\033[33m"
NIEBIESKI = "\033[34m"
RESET = "\033[0m"  # Przywraca domyślny kolor terminala


def display_solved(self, path: list[tuple[int, int]]) -> None:
    """Prints maze with solved path. """
    path_set = set(path)

    for y, row in enumerate(self.grid):
        for x, cell in enumerate(row):
            if (x, y) in path_set:
                if (x, y) == self.exit:
                    print(f"{CZERWONY}[.] {RESET}", end="")
                elif (x, y) == self.entry:
                    print(f"{CZERWONY}['] {RESET}", end="")
                else:
                    print(f"{ZIELONY}[{int(cell):X}]{RESET} ", end="")
            elif (x, y) not in self.locked_cells:
                print(f"[{int(cell):X}] ", end="")
            else:
                print(f"{NIEBIESKI}[_] {RESET}", end="")
        print()


def display_solved_labyrynth(self, path: list[tuple[int, int]]) -> None:
    """Prints solved maze with path, nicer look"""
    path_set: set[tuple[int, int]] = set(path)

    if not self.grid:
        return

    width = len(self.grid[0])

    EAST_MASK = 2
    SOUTH_MASK = 4

    print("+" + "---+" * width)

    for y, row in enumerate(self.grid):
        print("|", end="")

        for x, cell in enumerate(row):
            if (x, y) in self.locked_cells:
                content = f"{NIEBIESKI}[=]{RESET}"
            elif (x, y) in path_set:
                if (x, y) == self.exit:
                    content = f"{CZERWONY}EXT{RESET}"
                elif (x, y) == self.entry:
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

        print()  # Zakończenie rzędu


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

def display_unicode(self) -> None:
        """
        Draws the maze graphically in the terminal using Unicode characters.

        The canvas dimensions are expanded (2 characters per cell + 1 for the
        final wall). The entire canvas is initially filled with solid walls
        ('|').
        It then carves out empty spaces for the cells and the demolished walls
        using bitwise operations, skipping the locked '42' pattern cells.
        Finally, it marks the entry ('ST') and exit ('EX') points.
        """
    canvas_h = self.height * 2 + 1
    canvas_w = self.width * 2 + 1

    canvas = [['█' for _ in range(canvas_w)] for _ in range(canvas_h)]

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
            if char == '█':
                line += "██"
            elif char == ' ':
                line += "  "
            elif char == 'S':
                line += "ST"
            elif char == 'E':
                line += "EX"
        print(line)
