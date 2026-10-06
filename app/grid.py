from enum import Enum, auto

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
        self.cells: list[list[CellState]] = []
        self.clear()

    # def set_cell(self, x: int, y: int, state: CellState) -> None:
    #     if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
    #         self.cells[y][x] = state

    def clear(self) -> None:
        self.cells = [
            [CellState.WALL for _ in range(self.grid_width)]
            for _ in range(self.grid_height)
        ]



        for y in range(self.height):
            for x in range(self.width):
                self.cells[(y * 2) + 1][(x * 2) + 1] = CellState.FLOOR

        # TODO: add locked pattern
        for cx, cy in get_pattern_locked_cells(self.width, self.height):
            fx, fy = (cx * 2) + 1, (cy * 2) + 1
            self.cells[fy][fx] = CellState.LOCK


        en_x, en_y = self.m_entry
        self.cells[(en_y * 2) + 1][(en_x * 2) + 1] = CellState.ENTRY

        ex_x, ex_y = self.m_exit
        self.cells[(ex_y * 2) + 1][(ex_x * 2) + 1] = CellState.EXIT

    # TODO: draw solution path