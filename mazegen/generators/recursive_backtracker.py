import random
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


class RecursiveBacktracker(BaseGenerator):

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:

        untouched_cells, start_cell, _ = self._initialize_generator()

        path = [start_cell]

        while untouched_cells:
            current_cell = path[-1]
            next_cell = self.maze.pick_next_cell(current_cell, ~untouched_cells)

            if next_cell is not None:
                # add cell to path and maze
                untouched_cells &= ~(1 << next_cell)
                self.maze.flip_both_walls(current_cell, next_cell)
                path.append(next_cell)
                yield self.maze.get_coords_and_dir(current_cell, next_cell)
            # no possible moves, backtrack:
            else:
                path.pop()
