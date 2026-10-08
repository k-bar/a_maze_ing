import random
from typing import Generator

from mazegen import BaseGenerator
from mazegen.utils import Direction, get_pattern_locked_cells


class KruskalGenerator(BaseGenerator):
    """
    Disjoint-set (Union-Find) data structure.
    Used in graph theory to find the Minimum Spanning Tree (MST)
    and prevent the formation of cycles (loops).
    """

    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            seed: int | None = None
    ) -> None:
        """
        Initializes the structure storing the trees and their depths.

        Attributes:
            parent: A dictionary where each cell points to its parent cell.
                    It resembles a linked list. If a cell points to itself,
                    it is the root node of the tree (corridor).
            deep: A dictionary storing the "depth" (rank) of the tree,
            """
        super().__init__(width, height, m_entry, m_exit, perfect, seed)

        if seed is None:
            random.seed(seed)

        total_cells = width * height
        full_mask = (1 << total_cells) - 1

        self.walls_n: int = full_mask
        self.walls_e: int = full_mask
        self.walls_s: int = full_mask
        self.walls_w: int = full_mask

        self.parent: dict[tuple[int, int], tuple[int, int]] = {}
        self.deep: dict[tuple[int, int], int] = {}

        self.locked_cells: set[tuple[int, int]] = get_pattern_locked_cells(
            self.width, self.height)

        self.edges: list[tuple[int, int, str]] = []

        random.shuffle(self.edges)

        self._animation_iterator: \
            Generator[tuple[
                int, int, Direction], None, None] = self._algorithm_loop()

    def find(self, node: tuple[int, int]) -> tuple[int, int]:
        """
        Recursively finds the root node ("boss") for a given cell.
        It flattens the tree along the way (path compression) by
        assigning the found parent directly to the cell.

        Args:
            node: The cell for which the root node is being searched.

        Returns:
            The root parent of the set to which the cell belongs.
        """
        if self.parent[node] != node:
            self.parent[node] = self.find(self.parent[node])
        return self.parent[node]

    def union(self, node1: tuple[int, int], node2: tuple[int, int]) -> bool:
        """
        Merges two sets to which the given cells belong, optimizing
        the connection based on the depth (rank) of the trees.

        Args:
            node1: The first cell.
            node2: The second cell.

        Returns:
            bool: True if the cells belonged to different sets and the merge
                  was performed. False if the cells share the same parent
                  (are already connected), which would create a cycle (loop).
        """
        root1 = self.find(node1)
        root2 = self.find(node2)

        if root1 == root2:
            return False

        if self.deep[root1] > self.deep[root2]:
            self.parent[root2] = root1
        elif self.deep[root1] < self.deep[root2]:
            self.parent[root1] = root2
        else:
            self.parent[root1] = root2
            self.deep[root2] += 1

        return True

    def add(self, node: tuple[int, int]) -> None:
        """
        Adds a new cell as a new, separate set.

        Args:
            node: Coordinates of the cell to add.
        """
        self.parent[node] = node
        self.deep[node] = 0

    def prepare_kruskal(self) -> None:
        """
        Prepares the Union-Find data structure for Kruskal's algorithm.

        Adds every cell coordinates to the Union-Find structure as a separate
        set, skipping any coordinates belonging to the locked '42' pattern.
        """

        for y in range(self.height):
            for x in range(self.width):
                if (x, y) not in self.locked_cells:
                    self.add((x, y))

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """
        Generates the maze using a randomized Kruskal's algorithm.

        Collects all possible internal edges (West-East and North-South)
        excluding locked cells, shuffles them using the provided seed,
        and iterates through them. If an edge connects two disjoint sets,
        they are merged in the Union-Find structure and the dividing walls
        are demolished in the grid.

        Args:
            seed_val: A string seed used to initialize the random number
                      generator for reproducible maze layouts.
        """
        self.prepare_kruskal()

        random.seed(self.seed)

        edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for y in range(self.height):
            for x in range(self.width):
                if (x, y) in self.locked_cells:
                    continue

                if x + 1 < self.width and (x + 1, y) not in self.locked_cells:
                    edges.append(((x, y), (x + 1, y)))

                if y + 1 < self.height and (x, y + 1) not in self.locked_cells:
                    edges.append(((x, y), (x, y + 1)))

        random.shuffle(edges)

        for cell1, cell2 in edges:
            if self.union(cell1, cell2):
                x1, y1 = cell1
                x2, y2 = cell2

                dx = x2 - x1
                dy = y2 - y1

                cell_a = 1 << ((y1 * self.width) + x1)
                cell_b = 1 << ((y2 * self.width) + x2)

                if dx > 0:
                    self.walls_e &= ~cell_a
                    self.walls_w &= ~cell_b
                    yield x1, y1, Direction.EAST
                elif dx < 0:
                    self.walls_w &= ~cell_a
                    self.walls_e &= ~cell_b
                    yield x1, y1, Direction.WEST
                elif dy > 0:
                    self.walls_s &= ~cell_a
                    self.walls_n &= ~cell_b
                    yield x1, y1, Direction.SOUTH
                elif dy < 0:
                    self.walls_n &= ~cell_a
                    self.walls_s &= ~cell_b
                    yield x1, y1, Direction.NORTH
