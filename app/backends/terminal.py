import select
import sys
import time
import tty
import termios

from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.engine import AppController


class TerminalBackend(GraphicBackend):
    def __init__(self) -> None:
        pass

    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    def render_frame(self, grid: RenderGrid) -> None:

        state_to_char = {
            CellState.WALL: "#",
            CellState.FLOOR: " ",
            CellState.ENTRY: "S",
            CellState.EXIT: "E",
            CellState.PATH: "."
        }

        menu = (
            "\n=== A-Maze-ing Menu ==="
            "1: Regenerate maze | 2: Show/hide shortest path "
            "| 3: Rotate colors | 4: Quit"
            "Choice? (press key 1-4): "
        )
        lines: list[str] = []
        for y in range(grid.grid_height):
            row_chars = [state_to_char[cell] for cell in grid.cells[y]]
            lines.append("".join(row_chars))
        full_frame = "\033[H" + "\n".join(lines) + menu
        print(full_frame)

    @staticmethod
    def _is_key_pressed() -> bool:
        return select.select([sys.stdin], [], [], 0.0)[0] != []

    def start_loop(self, controller: "AppController") -> None:
        """Main loop with step by step animation"""

        # \033[?1049h   - enables alternative screen (no scrolling history)
        # \033[?25l     - hides blinking cursor
        print("\033[?1049h\033[?25l", end="", flush=True)
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while controller.is_running:
                controller.tick()
                self.render_frame(grid=controller.grid)
                if self._is_key_pressed():
                    key = sys.stdin.read(1)
                    if key == "4":
                        controller.handle_action("quit")
                    elif key == "1":
                        controller.handle_action("regen")
                time.sleep(0.04)
        finally:  # Execute Around Pattern
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\033[?1049l\033[?25h", end="", flush=True)
