from mazegen.maze_class import Maze


def path_to_directions(maze: 'Maze') -> str:
    """Convert List od Tuples to NEWS ;)"""
    if not maze.path or len(maze.path) < 2:
        return ""

    # znowu dict:
    directions = {
        (0, -1): "N",
        (1, 0): "E",
        (0, 1): "S",
        (-1, 0): "W"
    }

    moves = []
    temp_path = maze.path
    for i in range(len(temp_path) - 1):
        x1, y1 = temp_path.pop(0)
        x2, y2 = temp_path[0]

        dx = x2 - x1
        dy = y2 - y1

        moves.append(directions[(dx, dy)])

    return "".join(moves)


def export_to_file(maze: 'Maze') -> None:
    """Export maze, ENTRY, EXIT, and path to file."""
    if not maze.path or not maze.output_file:
        return

    try:
        with open(maze.output_file, "w", encoding="utf-8") as file:
            for row in maze.grid:
                line = "".join(str(f"{int(cell):X}") for cell in row)
                file.write(f"{line}\n")

            file.write("\n")
            file.write(f"{maze.m_entry[0]},{maze.m_entry[1]}\n")
            file.write(f"{maze.m_exit[0]},{maze.m_exit[1]}\n")
            directions = path_to_directions(maze)
            file.write(f"{directions}")

    except OSError as e:
        print(e)
