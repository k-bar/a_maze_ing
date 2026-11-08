import re
import subprocess
import sys
from typing import Literal, Any
from mazegen.utils import get_pattern_locked_cells
import typing

try:
    from pydantic import (BaseModel, Field, ValidationError,
                          model_validator, field_validator)
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
        SEED (int): Random seed used for generation reproducible results.
        ALGORITHM (str): The maze generation algorithm to use.
        ANIMATION (bool): If True, enables solving/generation animation.
        COLOR (str): Primary color for rendering.
        DISPLAY_MODE (str): Output mode (e.g., MLX or Terminal).
    """
    WIDTH: int = Field(..., ge=2, le=1000)
    HEIGHT: int = Field(..., ge=2, le=1000)
    ENTRY: tuple[int, int] = Field(default=(0, 0))
    EXIT: tuple[int, int] = Field(default=(1, 1))
    OUTPUT_FILE: str = Field(default="maze.txt", min_length=1, max_length=80)
    PERFECT: bool = Field(default=True)

    SEED: int | None = Field(default=None)
    SOLVER: Literal["BFS", "DFS", "ASTAR"] = (Field(default="BFS"))

    ALGORITHM: Literal[
        "KRUSKAL", "PRIM", "BACKTRACKER", "WILSON", "PRIM"] = Field(
        default="KRUSKAL")

    ANIMATION: bool = Field(default=True)
    COLOR: str = Field(default="green", min_length=1, max_length=80)
    DISPLAY_MODE: str = Field(default="MLX", min_length=1, max_length=80)

    WINDOW_WIDTH: int | None = Field(default=None, ge=640, le=7680)
    WINDOW_HEIGHT: int | None = Field(default=None, ge=480, le=4320)

    @field_validator("SEED", mode="before")
    @classmethod
    def empty_str_to_none(cls, value: str) -> str | None:
        if value == "":
            return None
        return value

    @field_validator("DISPLAY_MODE", mode="before")
    @classmethod
    def force_uppercase_mode(cls, value: str) -> str:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode='after')
    def validate_config(self) -> 'Config':
        """
        Ensures that the ENTRY and EXIT coordinates are within the
        boundaries defined by WIDTH and HEIGHT.
        """

        def entry_exit(point: tuple[int, int], height: int,
                       width: int) -> bool:
            x, y = point
            if not (0 <= x < width) or not (0 <= y < height):
                raise ValueError(f"is out of bounds for a "
                                 f"{self.WIDTH}x{self.HEIGHT} maze!")
            elif (x, y) in get_pattern_locked_cells(width, height):
                raise ValueError("is in '42' pattern!")
            else:
                return True

        try:
            entry_exit(self.ENTRY, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Point ENTRY {e}")

        try:
            entry_exit(self.EXIT, self.HEIGHT, self.WIDTH)
        except ValueError as e:
            raise ValueError(f"Point EXIT {e}")

        if self.DISPLAY_MODE == "TERMINAL":
            cols, lines = _get_terminal_bounds()

            max_w = (cols - 1) // 4
            max_h = (lines - 1 - 6) // 2

            if self.WIDTH > max_w or self.HEIGHT > max_h:
                raise ValueError(
                    f"Maze {self.WIDTH}x{self.HEIGHT} is too big for your "
                    f"console window ({cols}x{lines})! "
                    f"Maximum available size in this window "
                    f"is: {max_w}x{max_h}."
                )

        elif self.DISPLAY_MODE == "MLX":

            if self.WINDOW_WIDTH and self.WINDOW_HEIGHT:
                win_w, win_h = self.WINDOW_WIDTH, self.WINDOW_HEIGHT
            else:
                scr_w, scr_h = _get_screen_resolution_fallback()
                win_w = int(scr_w * 0.9)
                win_h = int(scr_h * 0.9)

            hud_h = 60
            available_h = win_h - hud_h

            block_min_size = 1

            max_w = (win_w - 1) // (block_min_size + 1)
            max_h = (available_h - 1) // (block_min_size + 1)

            if self.WIDTH > max_w or self.HEIGHT > max_h:
                raise ValueError(
                    f"Maze {self.WIDTH}x{self.HEIGHT} is exceeding "
                    f"render limits for dynamic window {win_w}x{win_h}!"
                    f"Maximum available size is {max_w}x{max_h}"
                )

        return self


def read_config(name: str) -> Config:
    """
    Opens and reads a configuration file.

    Args:
        name: The path to the configuration file.

    Returns:
        Config: A validated Config instance, or exits the program
                       if a file reading error occurs.
    """
    try:
        with open(name, "r", encoding='utf-8') as f:
            return read_and_parse(f)
    except OSError as e:
        print(f"Error opening file '{name}': {e}", file=sys.stderr)
        sys.exit(1)


def read_and_parse(file: typing.IO[str]) -> Config:
    """
    Parses the configuration content and converts it into a Config object.

    Expects lines in the format 'KEY = VALUE'. It ignores empty lines and
    comments starting with '#'. It specifically intercepts 'ENTRY' and 'EXIT'
    keys to cast their string values (e.g., "0,0") into tuples before passing
    them to the Pydantic model for validation.

    Args:
        file: An iterable text I/O stream containing the raw config data.

    Returns:
        Config: A fully instantiated Configuration object, or exits
                       the program upon validation failure or empty data.
    """
    config_data: dict[str, Any] = {}

    for line in file:
        clean_line = line.strip()
        if not clean_line or clean_line.startswith("#"):
            continue

        if "=" in clean_line:
            key, val = clean_line.split("=", 1)
            key, val = key.strip(), val.strip()

            if key in ["ENTRY", "EXIT"] and "," in val:
                try:
                    parsed_val = tuple(map(int, val.split(",")))
                    config_data[key] = parsed_val
                    continue
                except ValueError as e:
                    print(f"ENTRY/EXIT are invalid! \n {e}", file=sys.stderr)
                    sys.exit(1)

            if key in ["WINDOW_WIDTH", "WINDOW_HEIGHT"]:
                try:
                    config_data[key] = int(val)
                    continue
                except ValueError:
                    pass

            config_data[key] = val

    if config_data:
        try:
            config = Config.model_validate(config_data)
            print("Configuration loaded successfully:\n")
            return config

        except ValidationError as e:
            print("Error validating configuration file:\n", file=sys.stderr)
            print(e)
            sys.exit(1)
    else:
        print("Configuration file is empty or has no data "
              "in the format KEY=VALUE.", file=sys.stderr)
        sys.exit(1)


def _get_terminal_bounds() -> tuple[int, int]:
    import os
    import sys
    for fd in (sys.stderr, sys.stdin, sys.stdout):
        try:
            if fd and hasattr(fd, "fileno"):
                size = os.get_terminal_size()
                return size.columns, size.lines
        except OSError:
            continue
    try:
        with open('/dev/tty', 'r') as tty:
            size = os.get_terminal_size(tty.fileno())
            return size.columns, size.lines
    except (OSError, PermissionError):
        return 80, 24


def _get_screen_resolution_fallback() -> tuple[int, int]:
    try:
        output = subprocess.check_output("xrandr 2>/dev/null |"
                                         " grep 'current'",
                                         shell=True, text=True)
        match = re.search(r"current\s+(\d+)\s*x\s*(\d+)", output)
        if match:
            return int(match.group(1)), int(match.group(2))

    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return 1280, 720
