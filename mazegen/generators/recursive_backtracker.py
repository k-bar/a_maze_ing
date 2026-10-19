import random
from typing import Generator

from ..maze_model import Maze
from mazegen.utils import Direction, get_pattern_locked_cells


class RecursiveBacktracker(Maze):
    def __init__(self,
                 width: int,
                 height: int,
                 m_entry: tuple[int, int],
                 m_exit: tuple[int, int],
                 perfect: bool,
                 solver: str,
                 seed: int | None = None) -> None:
        super().__init__(width, height, m_entry, m_exit, perfect, solver, seed)

        if seed is None:
            random.seed(seed)

        total_cells = width * height
        full_mask = (1 << total_cells) - 1

        self.walls_n: int = full_mask
        self.walls_e: int = full_mask
        self.walls_s: int = full_mask
        self.walls_w: int = full_mask

        self.locked_cells: set[tuple[int, int]] = get_pattern_locked_cells(
            self.width, self.height)
        self.locked_cells_mask: int = 0
        for x, y in self.locked_cells:
            self.locked_cells_mask |= (1 << y * self.width + x)

        self._animation_iterator: Generator[
            tuple[int, int, Direction], None, None] = self._algorithm_loop()

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def pick_next_cell(self, cell: int, untouched_cells: int) -> int | None:

        moves = [d for d in Direction if
                 super().is_move_possible(cell, d, ~untouched_cells)]
        if not moves:
            return None
        picked_direction = random.choice(moves)
        return super().next_index(cell, picked_direction)

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:

        max_cells = self.width * self.height
        untouched_cells = (1 << max_cells) - 1
        untouched_cells &= ~self.locked_cells_mask
        start_cell = super().pick_random_cell(untouched_cells, max_cells)
        assert start_cell is not None
        untouched_cells &= ~(1 << start_cell)

        path = [start_cell]

        while untouched_cells:
            current_cell = path[-1]
            next_cell = self.pick_next_cell(current_cell, untouched_cells)

            # no possible moves, backtrack:
            if next_cell is not None:
                # add cell to path and maze
                untouched_cells &= ~(1 << next_cell)
                super().flip_both_walls(current_cell, next_cell)
                path.append(next_cell)
                yield super().get_coords_and_dir(current_cell, next_cell)
            else:
                path.pop()
