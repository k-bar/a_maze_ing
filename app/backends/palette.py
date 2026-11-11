import colorsys
import random
from dataclasses import dataclass
from typing import Self

from app.grid import CellState

type RGB = tuple[int, int, int]


@dataclass(frozen=True)
class MazePalette:
    wall: RGB
    floor: RGB
    entry: RGB
    exit_c: RGB
    path: RGB
    lock: RGB

    def get_rgb(self, state: CellState) -> RGB:
        match state:
            case CellState.FLOOR:
                return self.floor
            case CellState.ENTRY:
                return self.entry
            case CellState.EXIT:
                return self.exit_c
            case CellState.PATH:
                return self.path
            case CellState.LOCK:
                return self.lock
            case _:
                return self.wall

    @classmethod
    def generate_random_harmonized(cls) -> Self:
        """Generates coherent and contrast HSV palette"""
        base_h = random.random()

        wall_rgb = cls._hsv_to_rgb255(base_h, 0.75, 0.4)
        floor_rgb = cls._hsv_to_rgb255((base_h + 0.05) % 1.0, 0.15, 0.12)
        path_h = (base_h + 0.5) % 1.0
        path_rgb = cls._hsv_to_rgb255(path_h, 0.85, 0.95)
        entry_rgb = cls._hsv_to_rgb255((base_h + 0.33) % 1.0, 0.8, 0.8)
        exit_rgb = cls._hsv_to_rgb255((base_h + 0.66) % 1.0, 0.9, 0.8)
        lock_rgb = cls._hsv_to_rgb255((base_h + 0.15) % 1.0, 0.7, 0.9)

        return cls(wall_rgb, floor_rgb, entry_rgb, exit_rgb, path_rgb,
                   lock_rgb)

    @staticmethod
    def _hsv_to_rgb255(h: float, s: float, v: float) -> RGB:
        r, g, b = colorsys.hsv_to_rgb(h, s, v)
        return int(r * 255), int(g * 255), int(b * 255)


PRESETS = [
    MazePalette((128, 81, 37), (30, 30, 30), (0, 255, 0), (255, 0, 0),
                (0, 255, 255), (222, 217, 213)),
    MazePalette((38, 50, 56), (240, 233, 221), (0, 137, 123), (230, 74, 25),
                (21, 101, 192), (249, 168, 37)),
]
