import random
from ..maze_class import Maze
from ..maze_class import Wall


class UnionFind:
    """
    Disjoint-set (Union-Find) data structure.
    Used in graph theory to find the Minimum Spanning Tree (MST)
    and prevent the formation of cycles (loops).
    """

    def __init__(self) -> None:
        """
        Initializes the structure storing the trees and their depths.

        Attributes:
            parent: A dictionary where each cell points to its parent cell.
                    It resembles a linked list. If a cell points to itself,
                    it is the root node of the tree (corridor).
            deep: A dictionary storing the "depth" (rank) of the tree,
                  representing how many levels the tree contains.
        """
        self.parent: dict[tuple[int, int], tuple[int, int]] = {}
        self.deep: dict[tuple[int, int], int] = {}

    def add(self, node: tuple[int, int]) -> None:
        """
        Adds a new cell as a new, separate set.

        Args:
            node: Coordinates of the cell to add.
        """
        self.parent[node] = node
        self.deep[node] = 0

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



def _prepare_kruskal(maze: 'Maze') -> None:
    """
    Prepares the Union-Find data structure for Kruskal's algorithm.

    Adds every cell coordinates to the Union-Find structure as a separate
    set, skipping any coordinates belonging to the locked '42' pattern.
    """
    self.uf = UnionFind()

    for y in range(self.height):
        for x in range(self.width):
            if (x, y) not in self.locked_cells:
                self.uf.add((x, y))


def _generate_kruskal(self, seed_val: str | None) -> None:
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
    DIRECTION_MAP = {
        (1, 0): (Wall.E, Wall.W),
        (-1, 0): (Wall.W, Wall.E),
        (0, 1): (Wall.S, Wall.N),
        (0, -1): (Wall.N, Wall.S),
    }
    random.seed(seed_val)

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
        if self.uf.union(cell1, cell2):
            x1, y1 = cell1
            x2, y2 = cell2

            dx = x2 - x1
            dy = y2 - y1

            wall1, wall2 = DIRECTION_MAP[(dx, dy)]

            self.grid[y1][x1] &= ~wall1
            self.grid[y2][x2] &= ~wall2
