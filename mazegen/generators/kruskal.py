import random
from typing import Generator

from . import BaseGenerator
from mazegen.utils import Direction
from ..maze_model import Maze


class KruskalGenerator(BaseGenerator):

    def __init__(self, maze: Maze) -> None:
        super().__init__(maze)

        """
        Disjoint-set (Union-Find) data structure.
        Used in graph theory to find the Minimum Spanning Tree (MST)
        and prevent the formation of cycles (loops).
        """

        # A dictionary where each cell points to its parent cell.
        # It resembles a linked list. If a cell points to itself,
        # it is the root node of the tree (corridor).
        self.parent: dict[tuple[int, int], tuple[int, int]] = {}

        # A dictionary storing the "depth" (rank) of the tree
        self.deep: dict[tuple[int, int], int] = {}
        self.edges: list[tuple[int, int, str]] = []

        random.shuffle(self.edges)

        self._animation_iterator = self._algorithm_loop()

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

        for y in range(self.maze.height):
            for x in range(self.maze.width):
                if (x, y) not in self.maze.locked_cells:
                    self.add((x, y))

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

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

        random.seed(self.maze.seed)

        edges: list[tuple[tuple[int, int], tuple[int, int]]] = []
        for y in range(self.maze.height):
            for x in range(self.maze.width):
                if (x, y) in self.maze.locked_cells:
                    continue

                if (x + 1 < self.maze.width
                        and (x + 1, y) not in self.maze.locked_cells):
                    edges.append(((x, y), (x + 1, y)))

                if (y + 1 < self.maze.height
                        and (x, y + 1) not in self.maze.locked_cells):
                    edges.append(((x, y), (x, y + 1)))

        random.shuffle(edges)

        for cell1, cell2 in edges:
            if self.union(cell1, cell2):
                x1, y1 = cell1
                x2, y2 = cell2

                dx = x2 - x1
                dy = y2 - y1

                cell_a = 1 << ((y1 * self.maze.width) + x1)
                cell_b = 1 << ((y2 * self.maze.width) + x2)

                if dx > 0:
                    self.maze.walls_e &= ~cell_a
                    self.maze.walls_w &= ~cell_b
                    yield x1, y1, Direction.EAST
                elif dx < 0:
                    self.maze.walls_w &= ~cell_a
                    self.maze.walls_e &= ~cell_b
                    yield x1, y1, Direction.WEST
                elif dy > 0:
                    self.maze.walls_s &= ~cell_a
                    self.maze.walls_n &= ~cell_b
                    yield x1, y1, Direction.SOUTH
                elif dy < 0:
                    self.maze.walls_n &= ~cell_a
                    self.maze.walls_s &= ~cell_b
                    yield x1, y1, Direction.NORTH
