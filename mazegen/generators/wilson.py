import random
from typing import Generator

from mazegen import BaseGenerator
from mazegen.utils import Direction, get_pattern_locked_cells


class WilsonGenerator(BaseGenerator):
    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            seed: int | None = None
    ) -> None:
        super().__init__(width, height, m_entry, m_exit, perfect, seed)

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

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        # TODO needed?
        random.seed(self.seed)

        max_cells = self.width * self.height
        untouched_cells = (1 << max_cells) - 1
        untouched_cells &= ~self.locked_cells_mask
        first_maze_cell = super().pick_random_cell(untouched_cells, max_cells)
        assert first_maze_cell is not None
        untouched_cells &= ~(1 << first_maze_cell)

        while untouched_cells:
            start_cell = super().pick_random_cell(untouched_cells, max_cells)
            assert start_cell is not None
            current_path = [start_cell]
            current_path_mask = (1 << start_cell)
            while True:
                current_cell = current_path[-1]
                next_cell = super().next_index(current_cell,
                                               super().pick_possible_direction(
                                                   current_cell,
                                                   self.locked_cells_mask))
                # part of maze:
                if not untouched_cells & (1 << next_cell):
                    self.flip_both_walls(current_cell, next_cell)
                    yield super().get_coords_and_dir(current_cell, next_cell)
                    while current_path:
                        cell = current_path.pop()
                        assert cell is not None
                        untouched_cells &= ~(1 << cell)
                    break
                # backtrack if loop
                elif current_path_mask & (1 << next_cell):
                    while current_path[-1] != next_cell:
                        assert (removed := current_path.pop()) is not None
                        current_path_mask &= ~(1 << removed)
                        previous_cell = current_path[-1]
                        assert previous_cell is not None
                        self.flip_both_walls(removed, previous_cell)
                        yield super().get_coords_and_dir(removed,
                                                         previous_cell)
                # normal wandering
                else:
                    current_path.append(next_cell)
                    current_path_mask |= (1 << next_cell)
                    self.flip_both_walls(current_cell, next_cell)
                    yield super().get_coords_and_dir(current_cell, next_cell)
