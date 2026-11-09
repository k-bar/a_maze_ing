import random
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

    def generate_all(self) -> None:
        print("wykrylem")
        valid_cells_mask, start_cell, max_cells = self._initialize_generator()

        maze_mask = (1 << start_cell)
        frontier_mask = 0

        width = self.maze.width
        locked_mask = self.maze.locked_cells_mask

        border_n = self.maze.border_masks[0]
        border_e = self.maze.border_masks[1]
        border_s = self.maze.border_masks[2]
        border_w = self.maze.border_masks[3]

        def add_new_frontiers(cell: int) -> None:
            nonlocal frontier_mask
            forbid_mask = maze_mask | ~valid_cells_mask | locked_mask

            if not (border_n & (1 << cell)):
                n_conn = cell - width
                if not (forbid_mask & (1 << n_conn)):
                    frontier_mask |= (1 << n_conn)

            if not (border_e & (1 << cell)):
                e_conn = cell + 1
                if not (forbid_mask & (1 << e_conn)):
                    frontier_mask |= (1 << e_conn)

            if not (border_s & (1 << cell)):
                s_conn = cell + width
                if not (forbid_mask & (1 << s_conn)):
                    frontier_mask |= (1 << s_conn)

            if not (border_w & (1 << cell)):
                w_conn = cell - 1
                if not (forbid_mask & (1 << w_conn)):
                    frontier_mask |= (1 << w_conn)

        add_new_frontiers(start_cell)

        while frontier_mask:
            current_cell = self.maze.pick_random_cell(frontier_mask, max_cells)
            add_new_frontiers(current_cell)

            possible_connections = []

            if not (border_n & (1 << current_cell)):
                n_idx = current_cell - width
                if maze_mask & (1 << n_idx): possible_connections.append(n_idx)
            if not (border_e & (1 << current_cell)):
                e_idx = current_cell + 1
                if maze_mask & (1 << e_idx): possible_connections.append(e_idx)
            if not (border_s & (1 << current_cell)):
                s_idx = current_cell + width
                if maze_mask & (1 << s_idx): possible_connections.append(s_idx)
            if not (border_w & (1 << current_cell)):
                w_idx = current_cell - 1
                if maze_mask & (1 << w_idx): possible_connections.append(w_idx)

            if not possible_connections:
                continue

            maze_cell = random.choice(possible_connections)

            self.maze.flip_both_walls(current_cell, maze_cell)

            maze_mask |= (1 << current_cell)
            frontier_mask &= ~(1 << current_cell)
