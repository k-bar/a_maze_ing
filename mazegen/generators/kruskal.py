import random
from typing import Generator

from . import BaseGenerator
from ..maze_model import Maze
from ..utils import Direction


class KruskalGenerator(BaseGenerator):

    def __init__(self, maze: Maze) -> None:
        """
        Disjoint-set (Union-Find) data structure.
        Used in graph theory to find the Minimum Spanning Tree (MST)
        and prevent the formation of cycles (loops).
        """
        super().__init__(maze)

        # A list where each cell index points to its parent cell index.
        # If a cell points to itself, it is the root node of the tree.
        self.parent: list[int] = []
        self.deep: list[int] = []

    def find(self, node: int) -> int:
        """
        Iteratively finds the root node ("boss") for a given cell.
        Flattens the tree along the way (path compression).
        """
        root = node
        while self.parent[root] != root:
            root = self.parent[root]

        while self.parent[node] != root:
            next_node = self.parent[node]
            self.parent[node] = root
            node = next_node

        return root

    def union(self, node1: int, node2: int) -> bool:
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

    def _setup_edges(self) -> list[tuple[int, int]]:

        width = self.maze.width
        height = self.maze.height
        total_cells = width * height

        self.parent = list(range(total_cells))
        self.deep = [0] * total_cells

        if self.maze.seed is not None:
            random.seed(self.maze.seed)

        locked_set = set(self.maze.locked_cells)

        edges: list[tuple[int, int]] = []
        for y in range(height):
            row_offset = y * width
            for x in range(width):
                if (x, y) in locked_set:
                    continue

                cell1 = row_offset + x
                if x + 1 < width and (x + 1, y) not in locked_set:
                    edges.append((cell1, cell1 + 1))

                if y + 1 < height and (x, y + 1) not in locked_set:
                    edges.append((cell1, cell1 + width))

        random.shuffle(edges)
        return edges

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        """
        Generates the maze using a randomized Kruskal's algorithm.
        """

        edges = self._setup_edges()

        for cell1, cell2 in edges:
            if self.union(cell1, cell2):
                self.maze.flip_both_walls(cell1, cell2)
                yield self.maze.get_coords_and_dir(cell1, cell2)

    def generate_all(self) -> None:
        edges = self._setup_edges()

        for cell1, cell2 in edges:
            if self.union(cell1, cell2):
                self.maze.flip_both_walls(cell1, cell2)
