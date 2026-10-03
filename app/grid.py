from enum import Enum, auto


class CellState(Enum):
    WALL = auto()
    FLOOR = auto()
    ENTRY = auto()
    EXIT = auto()
    PATH = auto()


class RenderGrid:
    """Source of truth about state of grid to render"""

    def __init__(self, width: int, height: int) -> None:
        self.grid_width = (width * 2) + 1
        self.grid_height = (height * 2) + 1

        self.cells: list[list[CellState]] = []
        self.clear()

    def set_cell(self, x: int, y: int, state: CellState) -> None:
        if 0 <= x < self.grid_width and 0 <= y < self.grid_height:
            self.cells[y][x] = state

    def clear(self) -> None:
        self.cells = [[CellState.WALL for _ in range(self.grid_width)] for _ in
                      range(self.grid_height)]
