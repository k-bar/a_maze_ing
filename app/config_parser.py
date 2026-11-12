import os
import re
import subprocess
import sys
from pathlib import Path
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
    WIDTH: int = Field(ge=4, le=455)
    HEIGHT: int = Field(ge=4, le=863)
    ENTRY: tuple[int, int] = Field()
    EXIT: tuple[int, int] = Field()
    OUTPUT_FILE: str = Field(min_length=1, max_length=80)
    PERFECT: bool = Field()

    SEED: int | None = Field(default=None)
    SOLVER: Literal["BFS", "DFS", "ASTAR"] = (Field(default="BFS"))

    ALGORITHM: Literal[
        "KRUSKAL", "PRIM", "BACKTRACKER", "WILSON"] = Field(
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

    @field_validator("DISPLAY_MODE", "ALGORITHM", "SOLVER", mode="before")
    @classmethod
    def force_uppercase_mode(cls, value: Any) -> Any:
        if isinstance(value, str):
            return value.strip().upper()
        return value

    @model_validator(mode='after')
    def validate_config(self) -> 'Config':
        """
        Ensures that the ENTRY and EXIT coordinates are within the
        boundaries defined by WIDTH and HEIGHT.
        """

        if (self.WIDTH <= 3 or self.HEIGHT <= 3) and not self.PERFECT:
            raise ValueError(
                f"Maze size {self.WIDTH}x{self.HEIGHT} is too small for "
                f"imperfect mode (minimum 4x4 required)."
            )

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

        if self.ENTRY == self.EXIT:
            raise ValueError("ENTRY and EXIT coordinates cannot be identical!")

        if self.DISPLAY_MODE == "TERMINAL":
            cols, lines = _get_terminal_bounds()

            max_w = (cols - 1) // 4 - 1
            max_h = (lines - 1 - 7) // 2

            if max_w < 3 or max_h < 3:
                raise ValueError(
                    f"Terminal window ({cols}x{lines}) is too small! "
                    f"Minimum required size is 17x15 characters."
                )

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

    @field_validator("OUTPUT_FILE")
    @classmethod
    def validate_output_file(cls, value: str) -> str:
        clean_path = value.strip()
        if not clean_path:
            raise ValueError("OUTPUT_FILE cannot be empty or whitespace only.")

        path = Path(clean_path)

        if path.exists() and path.is_dir():
            raise ValueError(
                f"OUTPUT_FILE '{clean_path}' is a directory, not a file."
            )

        parent_dir = path.parent
        if not parent_dir.exists():
            raise ValueError(
                f"Directory '{parent_dir}' for OUTPUT_FILE does not exist."
            )

        if not os.access(parent_dir, os.W_OK):
            raise ValueError(
                f"No write permissions in directory '{parent_dir}'."
            )

        if path.exists() and not os.access(path, os.W_OK):
            raise ValueError(
                f"File '{clean_path}' already exists and is read-only."
            )

        return clean_path


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
        raise ValueError(
            f"Error opening configuration file '{name}': {e}") from e


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
                    if len(parsed_val) != 2:
                        raise ValueError(
                            "Expected exactly two coordinates (X,Y).")
                    config_data[key] = parsed_val
                    continue
                except ValueError as e:
                    raise ValueError(
                        f"Invalid coordinates for {key} ('{val}'): {e}") from e

            if key in ["WINDOW_WIDTH", "WINDOW_HEIGHT"]:
                try:
                    config_data[key] = int(val)
                    continue
                except ValueError as e:
                    raise ValueError(
                        f"Invalid integer for {key} ('{val}'): {e}") from e
            config_data[key] = val

    if not config_data:
        raise ValueError(
            "Configuration file is empty or has no valid KEY=VALUE pairs.")

    try:
        config = Config.model_validate(config_data)
        print("Configuration loaded successfully:\n")
        return config

    except ValidationError as e:
        error_msgs = "; ".join(
            [f"{err['loc']}: {err['msg']}" for err in e.errors()])
        raise ValueError(
            f"Configuration validation failed -> {error_msgs}") from e


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
