from typing import Generator

from . import BaseGenerator
from ..utils import Direction


class PrimGenerator(BaseGenerator):

    def _algorithm_loop(self) -> \
            Generator[tuple[int, int, Direction], None, None]:
        valid_cells_mask, start_cell, max_cells = self._initialize_generator()

        maze_mask = (1 << start_cell)
        frontier_mask = 0

        def add_new_frontiers(cell: int) -> None:
            nonlocal frontier_mask
            forbid = maze_mask | ~valid_cells_mask
            new_frontiers = self.maze.gather_possible_neighbours(cell, forbid)
            frontier_mask |= sum(1 << f for f in new_frontiers)

        add_new_frontiers(start_cell)

        while frontier_mask:

            current_cell = self.maze.pick_random_cell(frontier_mask, max_cells)
            add_new_frontiers(current_cell)

            # break a wall toward maze
            maze_cell = self.maze.pick_next_cell(cell=current_cell,
                                                 forbidden=~maze_mask)
            if maze_cell is None:
                continue
            self.maze.flip_both_walls(current_cell, maze_cell)
            yield self.maze.get_coords_and_dir(current_cell, maze_cell)

            # remove cell from frontier and add it to maze
            maze_mask |= (1 << current_cell)
            frontier_mask &= ~(1 << current_cell)
