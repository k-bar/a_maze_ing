from enum import Enum


class Direction(Enum):
    NORTH = ("N", -1, 0, 0)
    EAST = ("E", 0, 1, 1)
    SOUTH = ("S", 1, 0, 2)
    WEST = ("W", 0, -1, 3)

    @property
    def label(self) -> str:
        return self.value[0]

    @property
    def dy(self) -> int:
        return self.value[1]

    @property
    def dx(self) -> int:
        return self.value[2]

    @property
    def bit_index(self) -> int:
        return self.value[3]
