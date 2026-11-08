from typing import Generator

from . import BaseGenerator
from mazegen.utils import Direction


class WilsonGenerator(BaseGenerator):

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:

        untouched_cells, _, max_cells = self._initialize_generator()

        while untouched_cells:
            start_cell = self.maze.pick_random_cell(mask=untouched_cells,
                                                    max_cells=max_cells)

            current_path = [start_cell]
            current_path_mask = (1 << start_cell)
            while True:
                current_cell = current_path[-1]
                next_cell = self.maze.next_index(
                    current_cell, self.maze.pick_possible_direction(
                        cell=current_cell,
                        forbidden=self.maze.locked_cells_mask))
                # part of maze:
                if not untouched_cells & (1 << next_cell):
                    self.maze.flip_both_walls(current_cell, next_cell)
                    yield self.maze.get_coords_and_dir(current_cell, next_cell)
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
                        self.maze.flip_both_walls(removed, previous_cell)
                        yield self.maze.get_coords_and_dir(removed,
                                                           previous_cell)
                # normal wandering
                else:
                    current_path.append(next_cell)
                    current_path_mask |= (1 << next_cell)
                    self.maze.flip_both_walls(current_cell, next_cell)
                    yield self.maze.get_coords_and_dir(current_cell, next_cell)
