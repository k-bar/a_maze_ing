from mazegen.maze_model import Maze, Wall


def path_to_directions(maze: Maze) -> str:
    """Convert List od Tuples to NEWS ;)"""
    if len(maze.path) < 2:
        return ""
    directions = {(0, -1): "N", (1, 0): "E", (0, 1): "S", (-1, 0): "W"}
    return "".join(
        directions[(x2 - x1, y2 - y1)]
        for (x1, y1), (x2, y2) in zip(maze.path, maze.path[1:])
    )


def export_to_file(maze: Maze) -> None:
    """Export maze, ENTRY, EXIT, and path to file."""

    try:
        with open("maze.txt", "w", encoding="utf-8") as file:

            wn, we, ws, ww = maze.get_walls()
            wall_flags = (
                (wn, Wall.N),
                (we, Wall.E),
                (ws, Wall.S),
                (ww, Wall.W),
            )

            def cell_state(cell_index: int, row_number: int) -> str:
                pos_mask = 1 << (cell_index + row_number * maze.width)
                cel_state = sum(
                    flag for mask, flag in wall_flags if mask & pos_mask
                )
                return f"{cel_state:X}"

            for row in range(maze.height):
                line = "".join(cell_state(x, row) for x in range(maze.width))
                file.write(f"{line}\n")

            file.write("\n")
            file.write(f"{maze.m_entry[0]},{maze.m_entry[1]}\n")
            file.write(f"{maze.m_exit[0]},{maze.m_exit[1]}\n")
            directions = path_to_directions(maze)
            file.write(f"{directions}")

    except OSError as e:
        print(e)
