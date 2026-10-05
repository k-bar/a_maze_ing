from abc import ABC, abstractmethod

from mazegen.utils import Direction


class BaseGenerator(ABC):
    @abstractmethod
    def __init__(
            self,
            width: int,
            height: int,
            m_entry: tuple[int, int],
            m_exit: tuple[int, int],
            perfect: bool,
            seed: int | None = None
    ) -> None:
        self.width = width
        self.height = height
        self.m_entry = m_entry
        self.m_exit = m_exit
        self.perfect = perfect
        self.seed = seed

    @abstractmethod
    def step(self) -> tuple[int, int, Direction] | None:
        """
        Performs exactly one logic step of wall breaking

        Returns: (x, y, local_mas) of the cell that was changed,
        None when algorithm finished its work
        """
        pass

    @abstractmethod
    def get_walls(self) -> tuple[int, int, int, int]:
        """Returns: 4 big logic bitmasks for walls of entire maze"""
        pass

    def generate_all(self) -> None:
        """Performs whole algorithm at once"""
        while self.step() is not None:
            pass
