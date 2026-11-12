import random
from dataclasses import dataclass, field
from typing import Generator

from . import BaseGenerator
from ..utils import Direction


@dataclass(slots=True)
class PrimState:
    """
    Dataclass representing the internal state of the randomized Prim's
    algorithm.

    Attributes:
        width (int): The width of the maze grid.
        border_masks (dict[int, int]): Masks defining the borders of the grid
        for each direction.
        locked_mask (int): Bitmask of cells that are locked and cannot be
        modified.
        maze_cells_set (set[int]): A set of cell indices that are already part
        of the maze.
        frontier_set (set[int]): A set of cell indices currently in the
        frontier (for quick lookups).
        frontier_list (list[int]): A list of cell indices currently in the
        frontier (for random choice).
    """
    width: int
    border_masks: dict[int, int]
    locked_mask: int

    maze_cells_set: set[int] = field(default_factory=set)
    frontier_set: set[int] = field(default_factory=set)
    frontier_list: list[int] = field(default_factory=list)

    def add_frontiers(self, cell: int) -> None:
        """
        Evaluates the neighbors of the given cell and adds valid ones to
        the frontier.

        Args:
            cell (int): The flat index of the cell whose neighbors are to
            be evaluated.
        """
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
    """
    Maze generator implementing the randomized Prim's algorithm.

    This algorithm expands the maze outward from a starting point by randomly
    selecting a cell from the "frontier" (cells adjacent to the maze) and
    connecting it to an existing maze cell.
    """

    def _setup_shared_state(self) -> PrimState:
        """
        Initializes the state of the algorithm with the starting cell and
        its frontiers.

        Returns:
            PrimState: The initialized state object for the algorithm.
        """
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
        """
        Generator method that executes Prim's algorithm step-by-step.

        Yields:
            tuple[int, int, Direction]: A tuple containing the coordinates
            of the two cells being connected and the direction of the
            connection.
        """

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
        """
        Executes the entire Prim's algorithm instantly to generate the full
        maze.

        Unlike `_algorithm_loop`, this method does not yield intermediate
        steps, making it significantly faster when visualization is not
        required.
        """
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
