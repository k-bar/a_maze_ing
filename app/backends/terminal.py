import io
import os
import select
import sys
import threading
import time
import tty
import termios
from queue import Empty, Queue
from typing import Any, Optional

import numpy as np

from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.engine import AppController

input_queue: Queue[str] = Queue()


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

            screen_x = x // 2 * 4
            if x % 2 != 0:
                screen_x += 1
            screen_y = y + 1

            cell_payload = f"\033[{screen_y};{screen_x + 1}H{content}"
            _real_output.write(cell_payload)

        _real_output.flush()

    def change_colors(self, controller: "AppController") -> None:
        if self.colors == palette1:
            self.colors = palette2
        else:
            self.colors = palette1
        for (y, x), state in np.ndenumerate(controller.grid.cells):
            controller.grid.register_change(x, y, state)

    def start_loop(self, controller: "AppController") -> None:
        """Main loop with step by step animation"""

        menu_y_position = len(controller.grid.cells) + 2
        try:
            setup_terminal()
            draw_menu(menu_y_position, controller)

            t = threading.Thread(target=input_thread_worker, daemon=True)
            t.start()

            while controller.is_running:
                controller.tick()
                self.render_frame(grid=controller.grid)
                try:
                    pressed_key = input_queue.get_nowait()
                except Empty:
                    pressed_key = None

                if pressed_key is not None:
                    if pressed_key == "\x03":
                        controller.is_running = False
                        break

                    key_lowered = pressed_key.lower()
                    should_refresh_menu = True

                    if key_lowered == "4":
                        controller.handle_action("quit")
                    elif key_lowered == "1":
                        controller.handle_action("regen")
                        self.render_frame(grid=controller.grid)
                    elif key_lowered == "a":
                        controller.handle_action("cycle_maze_generator")
                        self.render_frame(grid=controller.grid)
                    elif key_lowered == "5":
                        controller.handle_action("hide_toggle")
                    elif key_lowered == " ":
                        controller.handle_action("pause")
                    elif key_lowered == "3":
                        self.change_colors(controller)
                    elif pressed_key == '\x1b[C':
                        controller.handle_action("skip")
                    else:
                        should_refresh_menu = False

                    if should_refresh_menu:
                        draw_menu(menu_y_position, controller)

                time.sleep(0.01)
        except KeyboardInterrupt:
            pass
        finally:  # Execute Around Pattern
            restore_terminal()


# global stash for terminal settings
_original_terminal_settings: Optional[list[Any]] = None
_real_output = sys.stdout
_devnull_stream = io.StringIO()


def setup_terminal() -> None:
    global _original_terminal_settings
    fd = sys.stdin.fileno()

    # save original terminal state
    _original_terminal_settings = termios.tcgetattr(fd)

    # \033[?1049h   - enables alternative screen (no scrolling history)
    # \033[?25l     - hides blinking cursor
    # \033[2J       - clear screen
    # \033[1;1H     - cursor on starting position 1,1
    _real_output.write("\033[?1049h\033[?25l\033[2J\033[1;1H")
    _real_output.flush()
    termios.tcflush(fd, termios.TCIFLUSH)

    # keyboard cbreak mode (immediate read)
    tty.setraw(fd)

    sys.stdout = _devnull_stream
    sys.stderr = _devnull_stream


def restore_terminal() -> None:
    if _original_terminal_settings is not None:
        fd = sys.stdin.fileno()
        # termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSAFLUSH, _original_terminal_settings)

        sys.stdout = _real_output
        sys.stderr = sys.__stderr__

        sys.stdout.write("\033[?1049l\033[?25h")
        sys.stdout.flush()


def input_thread_worker() -> None:
    fd = sys.stdin.fileno()
    while True:
        try:
            b = os.read(fd, 1)
            if not b:
                break
            ch = b.decode('utf-8', errors='ignore')

            if ch == '\x1b':
                ready_seq_, _, _ = select.select([fd], [], [], 0.02)
                if ready_seq_:
                    b_rest = os.read(fd, 2)
                    ch += b_rest.decode('utf-8', errors='ingore')

            input_queue.put(ch)
        except OSError:
            break


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


def draw_menu(y_offset: int, ctrl: AppController) -> None:
    menu = (
        f"\033[{y_offset};1H\033[J\r\n"
        f"=== A-Maze-ing Menu ===\r\n"
        f" 1: Regenerate maze |"
        f" 2: Show/hide shortest path |"
        f" 3: Rotate colors |"
        f" 4: Quit\r\n"
        f" [A]lgorithm: {ctrl.algorithm_name} |"
        f" [S]olver: {ctrl.config.SOLVER}\r\n"
        f" SEED: {ctrl.current_seed} |"
        f" SIZE: {ctrl.width}x{ctrl.height} |"
        f" STATE: {ctrl.state.name}\r\n"
        f"\r\n Choice? (press key 1-4, A, S): \033[K"
    )
    _real_output.write(menu)
    _real_output.flush()


def get_terminal_dimensions(fallback: tuple[int, int] = (80, 24)) \
        -> tuple[int, int]:
    """Gets actual console size"""
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return fallback
