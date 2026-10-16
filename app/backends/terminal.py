import select
import sys
import time
import tty
import termios
from typing import Any, Optional

import numpy as np

from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.engine import AppController


class TerminalBackend(GraphicBackend):
    def __init__(self) -> None:
        self.colors: dict[str, str] = palette1

    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    def render_frame(self, grid: RenderGrid) -> None:

        while grid.changed:
            changed_cell = grid.changed.popleft()
            if not changed_cell:
                return
            x, y, state = changed_cell
            content = resolve_cell_content(x, y, state, self.colors)
            move_cursor(x, y)
            sys.stdout.write(content)
            sys.stdout.flush()

    def change_colors(self, controller: "AppController") -> None:
        if self.colors == palette1:
            self.colors = palette2
        else:
            self.colors = palette1
        for (y, x), state in np.ndenumerate(controller.grid.cells):
            controller.grid.register_change(x, y, state)

    def start_loop(self, controller: "AppController") -> None:
        """Main loop with step by step animation"""

        try:
            setup_terminal()
            draw_menu(len(controller.grid.cells) + 2)
            while controller.is_running:
                controller.tick()
                self.render_frame(grid=controller.grid)
                key = handle_input()
                if key:
                    if key.lower() == "4":
                        controller.handle_action("quit")
                    elif key.lower() == "1":
                        controller.handle_action("regen")
                    elif key.lower() == "5":
                        controller.handle_action("hide_toggle")
                    elif key.lower() == "3":
                        self.change_colors(controller)

                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:  # Execute Around Pattern
            restore_terminal()


def move_cursor(x: int, y: int) -> None:
    screen_x = x // 2 * 4
    if x % 2 != 0:
        screen_x += 1
    screen_y = y + 1
    sys.stdout.write(f"\033[{screen_y};{screen_x + 1}H")


# global stash for terminal settings
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


palette1: dict[str, str] = {
    "STYLE_RESET": "\033[0m",
    "STYLE_WALL": "\033[32m",  # green walls
    "STYLE_PATH": "\033[30m",  # black path
    "STYLE_ENTRY": "\033[34m",  # blue start
    "STYLE_EXIT": "\033[33m",  # yellow exit
    "STYLE_LOCK": "\033[31m"  # red lock
}

palette2: dict[str, str] = {
    "STYLE_RESET": "\033[0m",
    "STYLE_WALL": "\033[30m",  # black walls
    "STYLE_PATH": "\033[32m",  # green path
    "STYLE_ENTRY": "\033[33m",  # yellow start
    "STYLE_EXIT": "\033[34m",  # blue exit
    "STYLE_LOCK": "\033[36m"  # lock
}


def _resolve_corner(pal: dict[str, str]) -> str:
    return f"{pal['STYLE_WALL']}+{pal['STYLE_RESET']}"


def _resolve_vertical_wall(state: CellState, pal: dict[str, str]) -> str:
    if state == CellState.WALL:
        return f"{pal['STYLE_WALL']}|{pal['STYLE_RESET']}"
    if state == CellState.PATH:
        return f"{pal['STYLE_PATH']}0{pal['STYLE_RESET']}"
    return " "


def _resolve_horizontal_wall(state: CellState, pal: dict[str, str]) -> str:
    if state == CellState.WALL:
        return f"{pal['STYLE_WALL']}---{pal['STYLE_RESET']}"
    if state == CellState.PATH:
        return f"{pal['STYLE_PATH']} 0 {pal['STYLE_RESET']}"
    return "   "


def _resolve_room(state: CellState, pal: dict[str, str]) -> str:
    if state == CellState.PATH:
        return f"{pal['STYLE_PATH']} 0 {pal['STYLE_RESET']}"
    if state == CellState.ENTRY:
        return f"{pal['STYLE_ENTRY']} S {pal['STYLE_RESET']}"
    if state == CellState.EXIT:
        return f"{pal['STYLE_EXIT']} E {pal['STYLE_RESET']}"
    if state == CellState.LOCK:
        return f"{pal['STYLE_LOCK']}[$]{pal['STYLE_RESET']}"
    return "   "


def resolve_cell_content(x: int, y: int, state: CellState,
                         pal: dict[str, str]) -> str:
    is_x_even = (x % 2 == 0)
    is_y_even = (y % 2 == 0)

    if is_x_even and is_y_even:
        return _resolve_corner(pal)
    if is_x_even and not is_y_even:
        return _resolve_vertical_wall(state, pal)
    if not is_x_even and is_y_even:
        return _resolve_horizontal_wall(state, pal)
    return _resolve_room(state, pal)


def draw_menu(y_offset: int) -> None:
    menu = (
        "\n=== A-Maze-ing Menu ==="
        "1: Regenerate maze | 2: Show/hide shortest path "
        "| 3: Rotate colors | 4: Quit"
        "Choice? (press key 1-4): "
    )
    sys.stdout.write(f"\033[{y_offset};1H{menu}")
    sys.stdout.flush()
