import random
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


class PrimGenerator(BaseGenerator):

    def _algorithm_loop(self) -> Generator[
        tuple[int, int, Direction], None, None]:
        untouched_cells, start_cell, _ = self._initialize_generator()
        maze_mask = (1 << start_cell)
        frontier_mask = 0

        def add_new_frontiers(cell: int, forbidden: int) -> None:
            nonlocal frontier_mask
            new_frontiers = self.maze.gather_possible_neighbours(cell,
                                                                 forbidden)
            for f in new_frontiers:
                if f is None:
                    continue
                frontier_mask |= (1 << f)

        add_new_frontiers(start_cell, ~untouched_cells)

        while frontier_mask:
            current_cell = random_index(frontier_mask)

            assert current_cell is not None

            # break a wall toward maze
            maze_cell = self.maze.pick_next_cell(current_cell, ~maze_mask)
            assert maze_cell is not None
            self.maze.flip_both_walls(current_cell, maze_cell)
            yield self.maze.get_coords_and_dir(current_cell, maze_cell)

            maze_mask |= (1 << current_cell)
            frontier_mask &= ~(1 << current_cell)

            add_new_frontiers(current_cell, maze_mask | ~untouched_cells)


def random_index(n: int) -> int | None:
    if n == 0:
        return None
    indices = []
    index = 0
    while n > 0:
        if n & 1:
            indices.append(index)
        n >>= 1
        index += 1
    return random.choice(indices)
