import random
from dataclasses import dataclass, field
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class PrimState:
    width: int
    border_masks: dict[int, int]
    locked_mask: int

    maze_cells_set: set[int] = field(default_factory=set)
    frontier_set: set[int] = field(default_factory=set)
    frontier_list: list[int] = field(default_factory=list)

    def add_frontiers(self, cell: int) -> None:
        cell_bit = 1 << cell
        for d in Direction:
            if not (self.border_masks[d.bit_index] & cell_bit):
                n_idx = cell + d.get_flat_offset(self.width)
                if (n_idx not in self.maze_cells_set
                        and n_idx not in self.frontier_set
                        and not (self.locked_mask & (1 << n_idx))):
                    self.frontier_set.add(n_idx)
                    self.frontier_list.append(n_idx)


class PrimGenerator(BaseGenerator):

    def _setup_shared_state(self) -> PrimState:
        _, start_cell, _ = self._initialize_generator()
        state = PrimState(
            width=self.maze.width,
            border_masks=self.maze.border_masks,
            locked_mask=self.maze.locked_cells_mask,
        )
        state.maze_cells_set.add(start_cell)
        state.add_frontiers(start_cell)
        return state

    def _algorithm_loop(self) -> \
            Generator[tuple[int, int, Direction], None, None]:

        state = self._setup_shared_state()
        border_mask = self.maze.border_masks
        width = self.maze.width

        f_list = state.frontier_list
        f_set = state.frontier_set
        m_set = state.maze_cells_set
        add_frontiers_fn = state.add_frontiers

        while f_list:
            idx = random.randrange(len(f_list))
            current_cell = f_list[idx]

            f_list[idx] = f_list[-1]
            f_list.pop()
            f_set.remove(current_cell)

            if current_cell in m_set:
                continue

            m_set.add(current_cell)
            add_frontiers_fn(current_cell)

            curr_bit = 1 << current_cell
            possible_connections = []

            for d in Direction:
                if not (border_mask[d.bit_index] & curr_bit):
                    neighbor = current_cell + d.get_flat_offset(width)
                    if neighbor in m_set:
                        possible_connections.append(neighbor)

            if possible_connections:
                maze_cell = random.choice(possible_connections)
                self.maze.flip_both_walls(current_cell, maze_cell)
                yield self.maze.get_coords_and_dir(current_cell, maze_cell)

    def generate_all(self) -> None:
        state = self._setup_shared_state()
        border_mask = self.maze.border_masks
        width = self.maze.width

        f_list = state.frontier_list
        f_set = state.frontier_set
        m_set = state.maze_cells_set
        add_frontiers_fn = state.add_frontiers

        while f_list:
            idx = random.randrange(len(f_list))
            current_cell = f_list[idx]

            f_list[idx] = f_list[-1]
            f_list.pop()
            f_set.remove(current_cell)

            if current_cell in m_set:
                continue

            m_set.add(current_cell)
            add_frontiers_fn(current_cell)

            curr_bit = 1 << current_cell
            possible_connections = []

            for d in Direction:
                if not (border_mask[d.bit_index] & curr_bit):
                    neighbor = current_cell + d.get_flat_offset(width)
                    if neighbor in m_set:
                        possible_connections.append(neighbor)

            if possible_connections:
                maze_cell = random.choice(possible_connections)
                self.maze.flip_both_walls(current_cell, maze_cell)
