from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from app.grid import RenderGrid

if TYPE_CHECKING:
    from app.engine import AppController


class GraphicBackend(ABC):
    """Abstract base class for all graphic rendering backends.

    Defines the standard interface required by the AppController to
    initialize the display, handle the event loop, and render frames.

    Attributes:
        controller (AppController | None): Reference to the main application
        engine.
    """

    def __init__(self) -> None:
        """Initializes the graphic backend."""
        self.controller: Optional["AppController"] = None

    @abstractmethod
    def init_window(self, width: int, height: int, title: str) -> None:
        """Initializes the main display window or rendering surface.

        Args:
            width: Logical width of the maze.
            height: Logical height of the maze.
            title: The title of the window.
        """
        pass

    @abstractmethod
    def render_frame(self, grid: RenderGrid) -> None:
        """Renders the current state of the maze grid.

        Args:
            grid: The RenderGrid instance containing cell states to draw.
        """
        pass

    @abstractmethod
    def start_loop(self, controller: "AppController") -> None:
        """Starts the main application event and rendering loop.

        Args:
            controller: The main engine controller managing state and logic.
        """
        pass

    def update_geometry(self, width: int, height: int) -> None:
        """Updates internal geometry when logical maze dimensions change.

        Args:
            width: New logical maze width.
            height: New logical maze height.
        """
        pass
