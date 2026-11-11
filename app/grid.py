from collections import deque
from enum import Enum, auto

import numpy as np

from mazegen.utils import get_pattern_locked_cells


class CellState(Enum):
    WALL = auto()
    FLOOR = auto()
    ENTRY = auto()
    EXIT = auto()
    PATH = auto()
    LOCK = auto()


class RenderGrid:
    """Source of truth about state of grid to render"""

    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int]
    ) -> None:
        self.width = width
        self.height = height
        self.grid_width = (width * 2) + 1
        self.grid_height = (height * 2) + 1
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.cells = np.full(
            shape=(self.grid_height, self.grid_width),
            fill_value=CellState.FLOOR,
            dtype=object
        )
        self.changed: deque[tuple[int, int, CellState]] = deque()
        self.require_full_redraw = False
        self.clear()

    def clear(self) -> None:
        self.changed.clear()
        self.cells[:, :] = CellState.WALL
        self.cells[1::2, 1::2] = CellState.FLOOR

        for cx, cy in get_pattern_locked_cells(self.width, self.height):
            fx, fy = (cx * 2) + 1, (cy * 2) + 1
            # self.register_change(fx, fy, CellState.LOCK)
            self.cells[fy, fx] = CellState.LOCK

        en_x, en_y = self.m_entry
        # self.register_change((en_x * 2) + 1, (en_y * 2) + 1, CellState.ENTRY)
        self.cells[(en_y * 2) + 1, (en_x * 2) + 1] = CellState.ENTRY

        ex_x, ex_y = self.m_exit
        # self.register_change((ex_x * 2) + 1, (ex_y * 2) + 1, CellState.EXIT)
        self.cells[(ex_y * 2) + 1, (ex_x * 2) + 1] = CellState.EXIT
        self.require_full_redraw = True

    def register_change(self, x: int, y: int, state: CellState) -> None:
        self.cells[y, x] = state
        self.changed.append((x, y, state))

    def push_entire_grid_to_changed(self) -> None:
        self.changed.clear()
        yy, xx = np.mgrid[0:self.grid_height, 0:self.grid_width]
        self.changed.extend(
            zip(xx.ravel().tolist(), yy.ravel().tolist(),
                self.cells.ravel().tolist())
        )
