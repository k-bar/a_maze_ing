from __future__ import annotations
import sys
from typing import Literal
import typing
from enum import IntFlag


try:
    from pydantic import BaseModel, Field, ValidationError, model_validator
except ImportError:
    print("------>      pip install pydantic")
    sys.exit(1)


class Wall(IntFlag):
    N = 1  # 0001
    E = 2  # 0010
    S = 4  # 0100
    W = 8  # 1000

    ALL = 1 | 2 | 4 | 8


class Maze:
    def __init__(self, config: Config) -> None:
        self.width = config.WIDTH
        self.height = config.HEIGHT
        self.perfect = config.PERFECT
        self.entry = config.ENTRY
        self.exit = config.EXIT

        self.grid: list[list[Wall]] = [
            [Wall.ALL for _ in range(self.width)] for _ in range(self.height)
        ]

        self.locked_cells = set()
        self._forty_two()

    def display(self) -> None:
        for row in self.grid:
            print(f"{[int(cell) for cell in row]}")

    # drukowanie wartosci komorek, '_' dla zablokowanych

    def display_42(self) -> None:
        for y, row in enumerate(self.grid):
            for x, cell in enumerate(row):
                if (x, y) == self.entry:
                    print("[ ] ", end="")
                elif (x, y) == self.exit:
                    print("[.] ", end="")
                elif (x, y) not in self.locked_cells:
                    print(f"[{int(cell):X}] ", end="")
                else:
                    print("[_] ", end="")
            print()

    # funkcja blokujaca odpowiednie komorki self.grid dla napisu '42'
    # algorytmy trzeba bedzie blokowac

    def _forty_two(self) -> None:

        # Komórki do zablokowania dla napisu '42'
        pattern = [
            (-3, -2), (1, -2), (2, -2), (3, -2),
            (-3, -1), (3, -1),
            (-3, 0), (-2, 0), (-1, 0), (1, 0), (2, 0), (3, 0),
            (-1, 1), (1, 1),
            (-1, 2), (1, 2), (2, 2), (3, 2)
        ]

        # Warunek, gdy wymiary nie pozwolą obejsc napisu '42' z kazdej strony,
        # to nie zostanie on utworzony, i wyswietlimy komunikat. (strona 8)
        if self.width < 9 or self.height < 7:
            print("Size of the MAZE is too small to include '42' pattern!")
            return

        cx = self.width // 2
        cy = self.height // 2

        # dodawanie do locked_cells set()
        for dx, dy in pattern:
            loc_x, loc_y = cx + dx, cy + dy
            self.locked_cells.add((loc_x, loc_y))


class Config(BaseModel):
    # mandatory:
    WIDTH: int = Field(..., ge=2, le=1000)
    HEIGHT: int = Field(..., ge=2, le=1000)
    ENTRY: tuple[int, int] = Field(default=(0, 0))
    EXIT: tuple[int, int] = Field(default=(0, 0))
    OUTPUT_FILE: str | None = Field(default=None, min_length=1, max_length=80)
    PERFECT: bool = Field(default=True)

    SEED: str = Field(default="42", min_length=1, max_length=80)

    # Algorithms: KRUSKAL, PRIM, BACKTRACKER
    ALGORITHM: Literal["KRUSKAL", "PRIM", "BACKTRACKER"] = (
        Field(default="KRUSKAL"))

    # for bonus
    ANIMATION: bool = Field(default=True)
    COLOR: str = Field(default="green", min_length=1, max_length=80)

    # wish to have

    # Renderer modes: MLX, Terminal
    DISPLAY_MODE: str = Field(default="MLX", min_length=1, max_length=80)

    @model_validator(mode='after')
    def validate_config(self) -> 'Config':
        # Logika walidująca, czy ENTRY i EXIT nie wychodzą poza planszę
        def entry_exit(point: tuple[int, int], height: int,
                       width: int) -> bool:
            x, y = point
            if not (0 <= x < width) or not (0 <= y < height):
                raise ValueError(f"znajduje się poza planszą "
                                 f"{self.WIDTH}x{self.HEIGHT}!")
            else:
                return True

        try:
            entry_exit(self.ENTRY, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Punkt ENTRY {e}")

        try:
            entry_exit(self.EXIT, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Punkt EXIT {e}")

        return self


def read_config(name: str) -> Config | None:
    try:
        with open(name, "r", encoding='utf-8') as f:
            return read_and_parse(f)
    except OSError as e:
        print(f"Błąd otwierania pliku '{name}': {e}")
        sys.exit(1)


def read_and_parse(file: typing.IO[str]) -> None:
    config_data = {}

    # Wczytywanie pliku zakładając format: KEY: VALUE
    for line in file:
        clean_line = line.strip()
        # Ignorujemy puste linie oraz komentarze
        if not clean_line or clean_line.startswith("#"):
            continue

        if "=" in clean_line:
            key, val = clean_line.split("=", 1)
            key, val = key.strip(), val.strip()

            # Jeśli klucz to ENTRY lub EXIT, a wartość ma
            # przecinek (np. "0,0"),
            # parsujemy string "0,0" na tuplę (0, 0), żeby Pydantic
            # przyjął to bez błędu.
            if key in ["ENTRY", "EXIT"] and "," in val:
                try:
                    val = tuple(map(int, val.split(",")))
                except ValueError as e:
                    print(f"Punkt ENTRY/EXIT jest niepoprawny! \n {e}")
                    sys.exit(1)

            config_data[key] = val

    if config_data:
        try:
            # inicjacja obiektu config z rozpakowanego słownika config_data
            config = Config(**config_data)
            print("Konfiguracja załadowana pomyślnie:\n")
            return config

        except ValidationError as e:
            print("Błąd walidacji pliku konfiguracyjnego:\n")
            print(e)
            sys.exit(1)
    else:
        print("Plik konfiguracyjny jest pusty lub nie ma "
              "danych w formacie KLUCZ=WARTOŚĆ.")
        sys.exit(1)


def main() -> None:
    print("Hello from a-maze-ing!")

    if len(sys.argv) != 2:
        print("Usage: a_maze_ing.py config.txt")
        sys.exit(1)
    config = read_config(sys.argv[1])
    if config:
        print(config)
        print(config.model_dump_json(indent=2))
        maze = Maze(config)
        maze.display_42()
        # maze.display()
    sys.exit(0)


if __name__ == "__main__":
    main()
