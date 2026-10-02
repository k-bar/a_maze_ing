import select
import sys
import time
import tty
import termios
from typing import TYPE_CHECKING

from app.backends.base import GraphicBackend
from app.utils import Direction

if TYPE_CHECKING:
    from app.engine import AppController


class TerminalBackend(GraphicBackend):
    # def update_window(self, x: int, y: int, wall_mask: int) -> None:
    #     pass

    def __init__(self) -> None:
        self.buffer: list[list[str]] = []
        self.char_width: int = 0
        self.char_height: int = 0

    def init_window(self, width: int, height: int, title: str) -> None:
        self.char_width = (width * 2) + 1
        self.char_height = (height * 2) + 1
        self.buffer = [["#" for _ in range(self.char_width)] for _ in
                       range(self.char_height)]

    def update_cell_in_buffer(self, x: int, y: int, wall_mask: int) -> None:
        # center of the cell...
        cx = (x * 2) + 1
        cy = (y * 2) + 1
        # ...is always corridor (empty)
        self.buffer[cy][cx] = " "

        for bit_index, direction in enumerate(Direction):
            _, dy, dx = direction.value
            if (wall_mask & (1 << bit_index)) == 0:
                self.buffer[cy + dy][cx + dx] = " "

    def render_frame(self) -> None:
        menu = (
            "\n=== A-Maze-ing Menu ==="
            "1: Regenerate maze | 2: Show/hide shortest path "
            "| 3: Rotate colors | 4: Quit"
            "Choice? (press key 1-4): "
        )

        frame_lines = ["".join(row) for row in self.buffer]
        full_frame = "\033[H" + "\n".join(frame_lines) + menu
        print(full_frame)

    def _is_key_pressed(self) -> bool:
        return select.select([sys.stdin], [], [], 0.0)[0] != []

    def start_loop(self, controller: "AppController") -> None:
        print("\033[?1049h\033[?25l", end="", flush=True)
        old_settings = termios.tcgetattr(sys.stdin)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while controller.is_running:
                controller.tick()
                self.render_frame()
                if self._is_key_pressed():
                    key = sys.stdin.read(1)
                    if key == "4":
                        controller.handle_action("quit")
                    elif key == "1":
                        controller.handle_action("regen")
                time.sleep(0.04)
        finally:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)
            print("\033[?1049l\033[?25h", end="", flush=True)
