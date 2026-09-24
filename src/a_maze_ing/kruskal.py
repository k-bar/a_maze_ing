# minimalne drzewo rozpinające, bez cykli (petli) teoria grafow
class UnionFind:
    def __init__(self) -> None:
        # kazda komorka ma swoja nadrzedna komorke, rodzica, do ktorego
        # zostala dolaczona, troche taka linked lista,
        # jezeli sama sobie jest rodzicem, jest
        # glowna komorka drzewa (korytarza)
        self.parent: dict[tuple[int, int], tuple[int, int]] = {}
        # "glebokosc drzewa" czyli ile dane drzewo ma w sobie komorek
        self.deep: dict[tuple[int, int], int] = {}

    def add(self, node: tuple[int, int]) -> None:
        # dodaje komorke jako nowy pusty zbiór
        self.parent[node] = node
        self.deep[node] = 0

    def find(self, node: tuple[int, int]) -> tuple[int, int]:
        # szuka szefa danej komorki
        if self.parent[node] != node:
            # jezeli
            self.parent[node] = self.find(self.parent[node])
        # zwraca rodzica zbioru do ktorego nalezy dana komorka
        return self.parent[node]

    def union(self, node1: tuple[int, int], node2: tuple[int, int]) -> bool:
        # łączy dwa zbiory, zwraca:
        # True, gdy wykona polaczenia
        # False, gdy są już połączone i stworzyłoby to pętlę
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
