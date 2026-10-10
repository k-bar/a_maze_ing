import select
import sys
import time
import tty
import termios
from typing import Any, Optional
from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.engine import AppController


class TerminalBackend(GraphicBackend):
    def __init__(self) -> None:
        pass

    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    def render_frame(self, grid: RenderGrid) -> None:

        if not grid.cells:
            return

        state_to_char = {
            CellState.WALL: "#",
            CellState.FLOOR: " ",
            CellState.ENTRY: "S",
            CellState.EXIT: "E",
            CellState.PATH: "0",
            CellState.LOCK: "$"
        }

        menu = (
            "\n=== A-Maze-ing Menu ==="
            "1: Regenerate maze | 2: Show/hide shortest path "
            "| 3: Rotate colors | 4: Quit"
            "Choice? (press key 1-4): "
        )

        lines: list[str] = []
        for y, row in enumerate(grid.cells):

            row_chars: str = ""
            for x, cell in enumerate(row):

                if x % 2 == 0:
                    if y % 2 == 0:
                        content = "\033[32m+\033[0m"
                    else:
                        if state_to_char[cell] == "#":
                            content = "\033[32m|\033[0m"
                        elif state_to_char[cell] == "0":
                            content = "\033[30m0\033[0m"
                        else:
                            content = " "
                else:
                    if y % 2 == 0:
                        if state_to_char[cell] == "#":
                            content = "\033[32m---\033[0m"
                        elif state_to_char[cell] == "0":
                            content = "\033[30m 0 \033[0m"
                        else:
                            content = "   "
                    else:
                        if state_to_char[cell] == "S":
                            content = "\033[34m S \033[0m"
                        elif state_to_char[cell] == "E":
                            content = "\033[33m E \033[0m"
                        elif state_to_char[cell] == "$":
                            content = "\033[31m[$]\033[0m"
                        elif state_to_char[cell] == "0":
                            content = "\033[30m 0 \033[0m"
                        else:
                            content = "   "

                row_chars += content
            lines.append(row_chars)

        full_frame = "\033[H" + "\n".join(lines) + menu
        print(full_frame)

    def start_loop(self, controller: "AppController") -> None:
        """Main loop with step by step animation"""

        try:
            setup_terminal()
            while controller.is_running:
                controller.tick()
                self.render_frame(grid=controller.grid)
                key = handle_input()
                if key:
                    if key.lower() == "4":
                        controller.handle_action("quit")
                    elif key.lower() == "1":
                        controller.handle_action("regen")

                time.sleep(0.04)
        except KeyboardInterrupt:
            pass
        finally:  # Execute Around Pattern
            restore_terminal()


def move_cursor(x: int, y: int) -> None:
    sys.stdout.write(f"\033[{y};{x}H")


_original_terminal_settings: Optional[list[Any]] = None


def setup_terminal() -> None:
    global _original_terminal_settings
    fd = sys.stdin.fileno()

    # save original terminal state
    _original_terminal_settings = termios.tcgetattr(fd)

    # keyboard cbreak mode (immediate read)
    tty.setcbreak(fd)

    # \033[?1049h   - enables alternative screen (no scrolling history)
    # \033[?25l     - hides blinking cursor
    # \033[2J       - clear screen
    # \033[1;1H     - cursor on starting position 1,1
    sys.stdout.write("\033[?1049h\033[?25l\033[2J\033[1;1H")
    sys.stdout.flush()


def restore_terminal() -> None:
    if _original_terminal_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSADRAIN, _original_terminal_settings)
        sys.stdout.write("\033[?1049l\033[?25h")
        sys.stdout.flush()


def handle_input() -> str:
    fd = sys.stdin.fileno()
    ready_to_read, _, _ = select.select([fd], [], [], 0.0)
    if ready_to_read:
        return sys.stdin.read(1)
    return ""
