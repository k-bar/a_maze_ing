from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from app.grid import RenderGrid

if TYPE_CHECKING:
    from app.engine import AppController


class GraphicBackend(ABC):
    @abstractmethod
    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    @abstractmethod
    def render_frame(self, grid: RenderGrid) -> None:
        pass

    @abstractmethod
    def start_loop(self, controller: "AppController") -> None:
        pass

    def update_geometry(self, width: int, height: int) -> None:
        pass
