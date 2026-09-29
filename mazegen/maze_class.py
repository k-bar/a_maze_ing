from __future__ import annotations
from collections import deque
import random
from src.config_parser import Config
from enum import IntFlag
from .kruskal import UnionFind

# Definiowanie kodów kolorów
CZERWONY = "\033[31m"
ZIELONY = "\033[32m"
ZOLTY = "\033[33m"
NIEBIESKI = "\033[34m"
RESET = "\033[0m"  # Przywraca domyślny kolor terminala


class Wall(IntFlag):
    """
    Bitwise flags representing the walls of a single maze cell.
    """
    N = 1  # 0001
    E = 2  # 0010
    S = 4  # 0100
    W = 8  # 1000

    ALL = 1 | 2 | 4 | 8


class Maze:
    """
    Represents the maze grid and handles its generation and display.

    Attributes:
        width: The width of the maze.
        height: The height of the maze.
        perfect: Boolean indicating if the maze should be perfect (no loops).
        entry: A tuple representing the (x, y) coordinates of the start.
        exit: A tuple representing the (x, y) coordinates of the exit.
        grid: A 2D list storing the Wall flags for each cell.
        locked_cells: A set of (x, y) coordinates blocked for the '42' pattern.
    """

    def __init__(self, config: Config) -> None:
        """
        Initializes the Maze using the provided configuration.

        Args:
            config: A validated Config object containing maze parameters.
        """
        self.width = config.WIDTH
        self.height = config.HEIGHT
        self.perfect = config.PERFECT
        self.entry = config.ENTRY
        self.exit = config.EXIT
        self.seed = config.SEED

        self.grid: list[list[Wall]] = [
            [Wall.ALL for _ in range(self.width)] for _ in range(self.height)
        ]

        self.locked_cells = set()
        self._forty_two()
        self.path = []
        self.output_file = config.OUTPUT_FILE

        if config.ALGORITHM == "KRUSKAL":
            self._prepare_kruskal()
            self._generate_kruskal(self.seed)

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

    def _prepare_kruskal(self) -> None:
        """
        Prepares the Union-Find data structure for Kruskal's algorithm.

        Adds every cell coordinates to the Union-Find structure as a separate
        set, skipping any coordinates belonging to the locked '42' pattern.
        """
        self.uf = UnionFind()

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.locked_cells:
                    self.uf.add((x, y))

    def _generate_kruskal(self, seed_val: str) -> None:
        """
        Generates the maze using a randomized Kruskal's algorithm.

        Collects all possible internal edges (West-East and North-South)
        excluding locked cells, shuffles them using the provided seed,
        and iterates through them. If an edge connects two disjoint sets,
        they are merged in the Union-Find structure and the dividing walls
        are demolished in the grid.

        Args:
            seed_val: A string seed used to initialize the random number
                      generator for reproducible maze layouts.
        """
        DIRECTION_MAP = {
            (1, 0): (Wall.E, Wall.W),
            (-1, 0): (Wall.W, Wall.E),
            (0, 1): (Wall.S, Wall.N),
            (0, -1): (Wall.N, Wall.S),
        }
        random.seed(seed_val)

        edges: list[tuple[int, int], tuple[int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.locked_cells:
                    continue

                if x + 1 < self.width and (x + 1, y) not in self.locked_cells:
                    edges.append(((x, y), (x + 1, y)))

                if y + 1 < self.height and (x, y + 1) not in self.locked_cells:
                    edges.append(((x, y), (x, y + 1)))

        random.shuffle(edges)

        for cell1, cell2 in edges:
            if self.uf.union(cell1, cell2):
                x1, y1 = cell1
                x2, y2 = cell2

                dx = x2 - x1
                dy = y2 - y1

                wall1, wall2 = DIRECTION_MAP[(dx, dy)]

                self.grid[y1][x1] &= ~wall1
                self.grid[y2][x2] &= ~wall2

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

    def _forty_two(self) -> None:
        """
        Blocks specific cells in the center of the grid to form a '42' shape.

        Algorithms building the maze must check `is_locked(x, y)` to avoid
        routing paths through these coordinates. If the maze dimensions are
        too small (width < 9 or height < 7) to enclose the pattern, it is
        aborted and a warning is printed.
        """
        pattern = [
            (-3, -2), (1, -2), (2, -2), (3, -2),
            (-3, -1), (3, -1),
            (-3, 0), (-2, 0), (-1, 0), (1, 0), (2, 0), (3, 0),
            (-1, 1), (1, 1),
            (-1, 2), (1, 2), (2, 2), (3, 2)
        ]

        if self.width < 9 or self.height < 7:
            print("Size of the MAZE is too small to include '42' pattern!")
            return

        cx = self.width // 2
        cy = self.height // 2

        for dx, dy in pattern:
            loc_x, loc_y = cx + dx, cy + dy
            self.locked_cells.add((loc_x, loc_y))

    def solver_dfs(self) -> list[tuple[int, int]]:
        """Find corridor from ENTRY to EXIT as DFS.
        """
        # kolejka do sprawdzania komorek
        stack = [self.entry]

        # odwiedzone, zeby nie sprawdzac dwa razy
        visited = {self.entry}

        # slownik a'la linked lista, key to gdzie jestem, value to skad
        # przyszedlem
        came_from = {self.entry: None}

        # mapa ruchow jak w DIRECTIONS, ale tutaj tupla jako wektor w key,
        # jedna sciana jako value
        moves = {
            (0, -1): Wall.N,  # Ruch w górę
            (1, 0): Wall.E,  # Ruch w prawo
            (0, 1): Wall.S,  # Ruch w dół
            (-1, 0): Wall.W  # Ruch w lewo
        }

        # glowna petla, FIFO, popleft wyciaga x, y z pierwszego elementu i go
        # usuwa z kolejki, krecimy sie w petli dopoki nie staniemy na EXIT
        while stack:
            current = stack.pop()

            if current == self.exit:
                break

            x, y = current

            # sprawdzamy sciany
            for (dx, dy), wall_flag in moves.items():
                nx, ny = x + dx, y + dy

                # zabezpieczenie na zewnetrzne sciany i na znak 42, chociaz
                # one tam sa wiec nie powinnismy wyjsc poza plansze
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and (nx, ny) not in self.locked_cells):

                    # bitowe porownanie sciany z moves, ze sciana w self.grid
                    if (self.grid[y][x] & wall_flag) == 0:

                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            came_from[(nx, ny)] = current
                            stack.append((nx, ny))

        # sciezka
        path = []
        curr = self.exit

        if curr not in came_from:
            print("?")
            return []

        while curr is not None:
            path.append(curr)
            curr = came_from[curr]

        # odwraca liste path, teraz entry jest jako pierwsze
        path.reverse()
        self.path = path
        return path

    def solver_bfs(self) -> list[tuple[int, int]]:
        """Find corridor from ENTRY to EXIT as BFS.
        """
        # kolejka do sprawdzania komorek (linked lista dwustronna)
        queue = deque([self.entry])

        # odwiedzone, zeby nie sprawdzac dwa razy
        visited = {self.entry}

        # slownik a'la linked lista, key to gdzie jestem, value to skad
        # przyszedlem
        came_from = {self.entry: None}

        # mapa ruchow jak w DIRECTIONS, ale tutaj tupla jako wektor w key,
        # jedna sciana jako value
        moves = {
            (0, -1): Wall.N,  # Ruch w górę
            (1, 0): Wall.E,  # Ruch w prawo
            (0, 1): Wall.S,  # Ruch w dół
            (-1, 0): Wall.W  # Ruch w lewo
        }

        # glowna petla, FIFO, popleft wyciaga x, y z pierwszego elementu
        # i go usuwa z kolejki, krecimy sie w petli dopoki nie staniemy na EXIT
        while queue:
            current = queue.popleft()

            if current == self.exit:
                break

            x, y = current

            # sprawdzamy sciany
            for (dx, dy), wall_flag in moves.items():
                nx, ny = x + dx, y + dy

                # zabezpieczenie na zewnetrzne sciany i na znak 42, chociaz
                # one tam sa wiec nie powinnismy wyjsc poza plansze
                if (0 <= nx < self.width and 0 <= ny < self.height
                        and (nx, ny) not in self.locked_cells):

                    # bitowe porownanie sciany z moves, ze sciana w self.grid
                    if (self.grid[y][x] & wall_flag) == 0:

                        if (nx, ny) not in visited:
                            visited.add((nx, ny))
                            came_from[(nx, ny)] = current
                            queue.append((nx, ny))

        # sciezka
        path = []
        curr = self.exit

        if curr not in came_from:
            print("?")
            return []

        while curr is not None:
            path.append(curr)
            curr = came_from[curr]

        # odwraca liste path, teraz entry jest jako pierwsze
        path.reverse()
        self.path = path
        return path

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

    def del_death_ends(self) -> None:
        """MASAKRA, ale wkoncu dziala, nie podobaja mi sie te dlugie warunki
        i tak mocno
        zaglebione cialo, ale dziala, mozna pomyslec jak to rozbic"""
        visited = set()
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.locked_cells:
                    cell = self.grid[y][x]
                    # zliczamy boolowskie jedynki
                    wall_count: int = (bool(cell & Wall.W)
                                       + bool(cell & Wall.E)
                                       + bool(cell & Wall.S)
                                       + bool(cell & Wall.N))

                    if wall_count == 3:
                        candidates = []
                        if ((cell & Wall.N) and y > 0 and (x, y - 1)
                                not in (self.locked_cells or visited)):
                            candidates.append((x, y - 1, Wall.N, Wall.S))
                        if ((cell & Wall.E) and x < self.width - 1 and
                                (x + 1, y) not in (self.locked_cells
                                                   or visited)):
                            candidates.append((x + 1, y, Wall.E, Wall.W))
                        if ((cell & Wall.S) and y < self.height - 1 and
                                (x, y + 1) not in (self.locked_cells
                                                   or visited)):
                            candidates.append((x, y + 1, Wall.S, Wall.N))
                        if ((cell & Wall.W) and x > 0 and (x - 1, y)
                                not in (self.locked_cells or visited)):
                            candidates.append((x - 1, y, Wall.W, Wall.E))

                        if candidates:
                            nx, ny, wall1, wall2 = random.choice(candidates)
                            self.grid[y][x] &= ~wall1
                            self.grid[ny][nx] &= ~wall2
                            visited.add((x, y))
        print(visited)

    def display_solved(self, path: list[tuple[int, int]]) -> None:
        """Drukuje labirynt ze ścieżką. """
        path_set = set(path)  # Set przyspiesza sprawdzanie 'in'

        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if (x, y) in path_set:
                    if (x, y) == self.exit:
                        print(f"{CZERWONY}[.] {RESET}", end="")
                        # sprawdza czy exit/entry zapisuja sie w path
                    elif (x, y) == self.entry:
                        print(f"{CZERWONY}['] {RESET}", end="")
                    else:
                        print(f"{ZIELONY}[{int(cell):X}]{RESET} ", end="")
                        # Ścieżka
                elif (x, y) not in self.locked_cells:
                    print(f"[{int(cell):X}] ", end="")  # pozostale
                else:
                    print(f"{NIEBIESKI}[_] {RESET}", end="")  # "42"
            print()
