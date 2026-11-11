from mazegen.maze_model import Maze, Wall


def path_to_directions(maze: Maze) -> str:
    """Convert List od Tuples to NEWS ;)"""
    if len(maze.path) < 2:
        return ""
    directions = {(0, -1): "N", (1, 0): "E", (0, 1): "S", (-1, 0): "W"}
    return "".join(
        directions.get((x2 - x1, y2 - y1), "")
        for (x1, y1), (x2, y2) in zip(maze.path, maze.path[1:])
    )


def export_to_file(maze: Maze, filename: str = "maze.txt") -> None:
    """Export maze, ENTRY, EXIT, and path to file."""

    with open(filename, "w", encoding="utf-8") as file:
        wn, we, ws, ww = maze.get_walls()
        wall_flags = (
            (wn, Wall.N),
            (we, Wall.E),
            (ws, Wall.S),
            (ww, Wall.W),
        )

        pos_mask = 1
        for _ in range(maze.height):
            row_chars: list[str] = []
            for _ in range(maze.width):
                cel_state = sum(
                    flag for mask, flag in wall_flags if mask & pos_mask
                )
                row_chars.append(f"{cel_state:X}")
                pos_mask <<= 1
            file.write("".join(row_chars) + "\n")

        file.write("\n")
        file.write(f"{maze.m_entry[0]},{maze.m_entry[1]}\n")
        file.write(f"{maze.m_exit[0]},{maze.m_exit[1]}\n")
        directions = path_to_directions(maze)
        file.write(f"{directions}")
