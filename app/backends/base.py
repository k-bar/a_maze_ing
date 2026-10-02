from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine import AppController


class GraphicBackend(ABC):
    @abstractmethod
    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    @abstractmethod
    def update_cell_in_buffer(self, x: int, y: int, wall_mask: int) -> None:
        pass

    @abstractmethod
    def render_frame(self) -> None:
        pass

    @abstractmethod
    def start_loop(self, controller: "AppController") -> None:
        pass
