from abc import abstractmethod, ABC


class BaseGenerator(ABC):
    @abstractmethod
    def __init__(self, width: int, height: int, seed: int) -> None:
        self.width = width
        self.height = height
        self.seed = seed

    @abstractmethod
    def step(self) -> tuple[int, int] | None:
        pass

    @abstractmethod
    def get_walls(self) -> tuple[int, int, int, int]:
        pass
