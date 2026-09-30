def path_to_directions(self) -> str:
    """Convert List od Tuples to NEWS ;)"""
    if not self.path or len(self.path) < 2:
        return ""

    # znowu dict:
    directions = {
        (0, -1): "N",
        (1, 0): "E",
        (0, 1): "S",
        (-1, 0): "W"
    }

    moves = []
    temp_path = self.path
    for i in range(len(temp_path) - 1):
        x1, y1 = temp_path.pop(0)
        x2, y2 = temp_path[0]

        dx = x2 - x1
        dy = y2 - y1

        moves.append(directions[(dx, dy)])

    return "".join(moves)


def export_to_file(self) -> None:
    """Export maze, ENTRY, EXIT, and path to file."""
    if not self.path or not self.output_file:
        return

    try:
        with open(self.output_file, "w", encoding="utf-8") as file:
            for row in self.grid:
                line = "".join(str(f"{int(cell):X}") for cell in row)
                file.write(f"{line}\n")

            file.write("\n")
            file.write(f"{self.entry[0]},{self.entry[1]}\n")
            file.write(f"{self.exit[0]},{self.exit[1]}\n")
            directions = self.path_to_directions()
            file.write(f"{directions}")

    except OSError as e:
        print(e)
