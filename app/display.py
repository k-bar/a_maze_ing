from mazegen.maze_model import Maze, Wall

# Colors for terminal output
CZERWONY = "\033[31m"
ZIELONY = "\033[32m"
ZOLTY = "\033[33m"
NIEBIESKI = "\033[34m"
RESET = "\033[0m"  # Resets the terminal color to default

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
