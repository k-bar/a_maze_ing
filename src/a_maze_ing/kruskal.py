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