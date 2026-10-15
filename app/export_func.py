from mazegen.maze_model import Maze, Wall


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
    temp_path = maze.path[:]
    for i in range(len(temp_path) - 1):
        x1, y1 = temp_path.pop(0)
        x2, y2 = temp_path[0]

        dx = x2 - x1
        dy = y2 - y1

        moves.append(directions[(dx, dy)])

    return "".join(moves)


def export_to_file(maze: Maze) -> None:
    """Export maze, ENTRY, EXIT, and path to file."""
    # if not maze.path
    #     return

    try:
        with open("maze.txt", "w", encoding="utf-8") as file:

            wn, we, ws, ww = maze.get_walls()

            def cell_state(cell_index: int, row_number: int) -> str:
                pos = cell_index + row_number * maze.width
                pos_mask = (1 << pos)
                n_wall = Wall.N if ((wn & pos_mask) != 0) else 0
                e_wall = Wall.E if ((we & pos_mask) != 0) else 0
                s_wall = Wall.S if ((ws & pos_mask) != 0) else 0
                w_wall = Wall.W if ((ww & pos_mask) != 0) else 0
                cel_state = n_wall + e_wall + s_wall + w_wall
                return str(f"{cel_state:X}")

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
