import sys
from typing import Literal
import typing

try:
    from pydantic import BaseModel, Field, ValidationError, model_validator
except ImportError:
    print("------>      pip install pydantic")
    sys.exit(1)


class Config(BaseModel):
    """
    Pydantic model representing the configuration for the maze generator.

    Attributes:
        WIDTH (int): The width of the maze. Mandatory.
        HEIGHT (int): The height of the maze. Mandatory.
        ENTRY (tuple): Starting coordinates (x, y). Default is (0, 0).
        EXIT (tuple): Target coordinates (x, y). Default is (0, 0).
        OUTPUT_FILE (str | None): File path to save the output.
        PERFECT (bool): If True, generates a perfect maze without loops.
        SEED (str): Random seed used for generation reproducible results.
        ALGORITHM (str): The maze generation algorithm to use.
        ANIMATION (bool): If True, enables solving/generation animation.
        COLOR (str): Primary color for rendering.
        DISPLAY_MODE (str): Output mode (e.g., MLX or Terminal).
    """
    WIDTH: int = Field(..., ge=2, le=1000)
    HEIGHT: int = Field(..., ge=2, le=1000)
    ENTRY: tuple[int, int] = Field(default=(0, 0))
    EXIT: tuple[int, int] = Field(default=(0, 0))
    OUTPUT_FILE: str | None = Field(default=None, min_length=1, max_length=80)
    PERFECT: bool = Field(default=True)

    SEED: str = Field(default="42", min_length=1, max_length=80)

    ALGORITHM: Literal["KRUSKAL", "PRIM", "BACKTRACKER"] = (
        Field(default="KRUSKAL"))

    ANIMATION: bool = Field(default=True)
    COLOR: str = Field(default="green", min_length=1, max_length=80)
    DISPLAY_MODE: str = Field(default="MLX", min_length=1, max_length=80)

    @model_validator(mode='after')
    def validate_config(self) -> 'Config':
        """
        Validates the configuration parameters post-initialization.

        Ensures that the ENTRY and EXIT coordinates are within the
        boundaries defined by WIDTH and HEIGHT.

        Returns:
            Config: The validated Config instance.

        Raises:
            ValueError: If the entry or exit points are out of bounds.
        """

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
    """
    Opens and reads a configuration file.

    Args:
        name: The path to the configuration file.

    Returns:
        Config | None: A validated Config instance, or exits the program
                       if a file reading error occurs.
    """
    try:
        with open(name, "r", encoding='utf-8') as f:
            return read_and_parse(f)
    except OSError as e:
        print(f"Błąd otwierania pliku '{name}': {e}")
        sys.exit(1)


def read_and_parse(file: typing.IO[str]) -> Config | None:
    """
    Parses the configuration content and converts it into a Config object.

    Expects lines in the format 'KEY = VALUE'. It ignores empty lines and
    comments starting with '#'. It specifically intercepts 'ENTRY' and 'EXIT'
    keys to cast their string values (e.g., "0,0") into tuples before passing
    them to the Pydantic model for validation.

    Args:
        file: An iterable text I/O stream containing the raw config data.

    Returns:
        Config | None: A fully instantiated Configuration object, or exits
                       the program upon validation failure or empty data.
    """
    config_data = {}

    for line in file:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue

        if "=" in clean_line:
            key, val = clean_line.split("=", 1)
            key, val = key.strip(), val.strip()

            if key in ["ENTRY", "EXIT"] and "," in val:
                try:
                    val = tuple(map(int, val.split(",")))
                except ValueError as e:
                    print(f"Punkt ENTRY/EXIT jest niepoprawny! \n {e}")
                    sys.exit(1)

            config_data[key] = val

    if config_data:
        try:
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