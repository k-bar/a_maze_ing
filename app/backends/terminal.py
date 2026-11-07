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
from app.backends.palette import MazePalette, PRESETS
from app.grid import RenderGrid, CellState
from app.engine import AppController

input_queue: Queue[str] = Queue()


class TerminalBackend(GraphicBackend):
    def __init__(self) -> None:
        super().__init__()
        self._last_grid_w: int = 0
        self._last_grid_h: int = 0
        self.controller: AppController | None = None
        self.palette: MazePalette = PRESETS[0]
        self.preset_mode = 0

    def init_window(self, width: int, height: int, title: str) -> None:
        pass

    def render_frame(self, grid: RenderGrid) -> None:

        if grid.width != self._last_grid_w or grid.height != self._last_grid_h:
            self._last_grid_w = grid.width
            self._last_grid_h = grid.height
            _real_output.write("\033[2J\033[1;1H")
            _real_output.flush()

            menu_y_position = len(grid.cells) + 2
            assert self.controller is not None
            draw_menu(menu_y_position, self.controller)

        while grid.changed:
            changed_cell = grid.changed.popleft()
            if not changed_cell:
                return
            x, y, state = changed_cell
            content = resolve_cell_content(x, y, state, self.palette)

            screen_x = x // 2 * 4
            if x % 2 != 0:
                screen_x += 1
            screen_y = y + 1

            cell_payload = f"\033[{screen_y};{screen_x + 1}H{content}"
            _real_output.write(cell_payload)

        _real_output.flush()

    def change_colors(self, controller: "AppController") -> None:

        self.preset_mode = (self.preset_mode + 1) % 5
        if self.preset_mode < len(PRESETS):
            self.palette = PRESETS[self.preset_mode]
        else:
            self.palette = MazePalette.generate_random_harmonized()
        for (y, x), state in np.ndenumerate(controller.grid.cells):
            controller.grid.register_change(x, y, state)

    def start_loop(self, controller: "AppController") -> None:
        """Main loop with step by step animation"""

        self.controller = controller
        cols, lines = get_terminal_dimensions()
        controller.max_width = (cols - 1) // 4 - 1
        controller.max_height = (lines - 1 - 7) // 2

        menu_y_position = len(controller.grid.cells) + 2
        try:
            setup_terminal()
            controller.tick()
            self.render_frame(grid=controller.grid)
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
                    if controller.is_entering_seed:
                        match pressed_key:
                            case "\x7f" | "\x08":
                                controller.handle_action("seed_backspace")
                            case "\r" | "\n":
                                controller.handle_action("enter_action")
                            case " ":
                                controller.handle_action("pause")
                            case _ if pressed_key.isdigit():
                                controller.handle_action(
                                    f"digit_{pressed_key}")
                            case _:
                                should_refresh_menu = False

                    else:
                        if key_lowered == "q":
                            controller.handle_action("quit")
                        elif key_lowered == "r":
                            controller.handle_action("regen")
                            self.render_frame(grid=controller.grid)
                        elif key_lowered == "a":
                            controller.handle_action("cycle_maze_generator")
                            self.render_frame(grid=controller.grid)
                        elif key_lowered == "s":
                            controller.handle_action("cycle_solver")
                        elif key_lowered == "h":
                            controller.handle_action("hide_toggle")
                        elif key_lowered == " ":
                            controller.handle_action("pause")
                        elif key_lowered == "k":
                            controller.handle_action("activate_seed_input")
                        elif key_lowered == "n":
                            controller.handle_action("randomize_seed")
                        elif key_lowered == "p":
                            controller.handle_action("toggle_perfect")
                            self.render_frame(grid=controller.grid)
                        elif key_lowered in ("+", "="):
                            controller.handle_action("speed_up")
                        elif key_lowered == "-":
                            controller.handle_action("speed_down")

                        elif key_lowered == "c":
                            self.change_colors(controller)
                        elif pressed_key in ["\x1b[4~", "\x1b[F", "\x1b[OF"]:
                            controller.handle_action("skip")
                        elif pressed_key == '\r' or pressed_key == '\n':
                            controller.handle_action("enter_action")
                            # TODO render?
                        elif pressed_key == '\t':
                            controller.handle_action("toggle_arrow_mode")
                        elif pressed_key in ['\x1b[A', '\x1b[B', '\x1b[C',
                                             '\x1b[D']:
                            action_name = ""
                            match pressed_key:
                                case '\x1b[A':
                                    action_name = "move_up"
                                case '\x1b[B':
                                    action_name = "move_down"
                                case '\x1b[C':
                                    action_name = "move_right"
                                case '\x1b[D':
                                    action_name = "move_left"
                            controller.handle_action(action_name)
                        else:
                            should_refresh_menu = False

                    if should_refresh_menu:
                        menu_y_position = len(controller.grid.cells) + 2
                        draw_menu(menu_y_position, controller)
                        self.render_frame(grid=controller.grid)

                time.sleep(0.01)

        except KeyboardInterrupt:
            pass

        finally:  # Execute Around Pattern
            restore_terminal()

    def update_geometry(self, width: int, height: int) -> None:
        pass


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


# palette1: dict[str, str] = {
#     "STYLE_RESET": "\033[0m",
#     "STYLE_WALL": "\033[32m",  # green walls
#     "STYLE_PATH": "\033[30m",  # black path
#     "STYLE_ENTRY": "\033[34m",  # blue start
#     "STYLE_EXIT": "\033[33m",  # yellow exit
#     "STYLE_LOCK": "\033[31m"  # red lock
# }
#
# palette2: dict[str, str] = {
#     "STYLE_RESET": "\033[0m",
#     "STYLE_WALL": "\033[30m",  # black walls
#     "STYLE_PATH": "\033[32m",  # green path
#     "STYLE_ENTRY": "\033[33m",  # yellow start
#     "STYLE_EXIT": "\033[34m",  # blue exit
#     "STYLE_LOCK": "\033[36m"  # lock
# }
#
#
# def _resolve_corner(pal: dict[str, str]) -> str:
#     return f"{pal['STYLE_WALL']}+{pal['STYLE_RESET']}"
#
#
# def _resolve_vertical_wall(state: CellState, pal: dict[str, str]) -> str:
#     if state == CellState.WALL:
#         return f"{pal['STYLE_WALL']}|{pal['STYLE_RESET']}"
#     if state == CellState.PATH:
#         return f"{pal['STYLE_PATH']}0{pal['STYLE_RESET']}"
#     return " "
#
#
# def _resolve_horizontal_wall(state: CellState, pal: dict[str, str]) -> str:
#     if state == CellState.WALL:
#         return f"{pal['STYLE_WALL']}---{pal['STYLE_RESET']}"
#     if state == CellState.PATH:
#         return f"{pal['STYLE_PATH']} 0 {pal['STYLE_RESET']}"
#     return "   "
#
#
# def _resolve_room(state: CellState, pal: dict[str, str]) -> str:
#     if state == CellState.PATH:
#         return f"{pal['STYLE_PATH']} 0 {pal['STYLE_RESET']}"
#     if state == CellState.ENTRY:
#         return f"{pal['STYLE_ENTRY']} S {pal['STYLE_RESET']}"
#     if state == CellState.EXIT:
#         return f"{pal['STYLE_EXIT']} E {pal['STYLE_RESET']}"
#     if state == CellState.LOCK:
#         return f"{pal['STYLE_LOCK']}[$]{pal['STYLE_RESET']}"
#     return "   "


def supports_truecolor() -> bool:
    if os.environ.get("COLORTERM") in ("truecolor", "24bit"):
        return True
    if "TERM_PROGRAM" in os.environ:
        return True
    return False


def rgb_to_ansi(r: int, g: int, b: int, is_bg: bool = False) -> str:
    """Returns TrueColor ANSI or safe fallback 16-colors"""
    if supports_truecolor():
        mode = 48 if is_bg else 38
        return f"\033[{mode};2;{r};{g};{b}m"
    ansi_base = 40 if is_bg else 30
    v = (r + g + b) // 3
    bright = 60 if v > 128 else 0
    if r > 200 and g > 200 and b > 200:
        return f"\033[{ansi_base + 7 + bright}m"
    if r < 50 and g < 50 and b < 50:
        return f"\033[{ansi_base + 0}m"
    if r > g and r > b:
        return f"\033[{ansi_base + 3 if g > 100 else ansi_base + 1 + bright}m"
    if g > r and g > b:
        return f"\033[{ansi_base + 3 if r > 100 else ansi_base + 2 + bright}m"
    if b > r and b > g:
        return f"\033[{ansi_base + 6 if g > 100 else ansi_base + 4 + bright}m"
    return f"\033[{ansi_base + 7}m"


def supports_utf8() -> bool:
    try:
        return sys.stdout.encoding.lower() in ("utf-8", "utf8", "cp65001")
    except AttributeError:
        return False


# def resolve_cell_content(x: int, y: int, state: CellState,
#                          palette: MazePalette) -> str:
#     is_x_even = (x % 2 == 0)
#     is_y_even = (y % 2 == 0)
#
#     rgb = palette.get_rgb(state)
#     reset = "\033[0m"
#
#     bg_ansi = rgb_to_ansi(rgb[0], rgb[1], rgb[2], is_bg=True)
#     text_color = "\033[30m" if (rgb[0] + rgb[1] + rgb[
#         2]) // 3 > 128 else "\033[37m"
#     cell_style = f"{bg_ansi}{text_color}"
#
#     if is_x_even and is_y_even:
#         # wall corners
#         wall_rgb = palette.get_rgb(CellState.WALL)
#         return f"{rgb_to_ansi(*wall_rgb, is_bg=True)}+{reset}"
#
#     if is_x_even and not is_y_even:
#         # vertical walls / paths
#         if state == CellState.WALL:
#             return f"{cell_style}|{reset}"
#         return f"{cell_style} {reset}"
#
#     if not is_x_even and is_y_even:
#         # horizontal walls / paths
#         if state == CellState.WALL:
#             return f"{cell_style}---{reset}"
#         return f"{cell_style}   {reset}"
#
#     # room
#     char = "   "
#     if state == CellState.ENTRY:
#         char = " S "
#     if state == CellState.EXIT:
#         char = " E "
#     if state == CellState.LOCK:
#         char = "[$]"
#     if state == CellState.PATH:
#         char = " • "
#
#     return f"{cell_style}{char}{reset}"


def resolve_cell_content(x: int, y: int, state: CellState,
                         palette: MazePalette) -> str:
    is_x_even = (x % 2 == 0)
    is_y_even = (y % 2 == 0)

    rgb = palette.get_rgb(state)
    reset = "\033[0m"

    bg_ansi = rgb_to_ansi(*rgb, is_bg=True)

    text_color = "\033[30m" if (rgb[0] + rgb[1] + rgb[
        2]) // 3 > 128 else "\033[37m"
    cell_style = f"{bg_ansi}{text_color}"

    has_utf8 = supports_utf8()

    # wall corners and walls
    if state == CellState.WALL:
        wall_rgb = palette.get_rgb(CellState.WALL)
        wall_bg = rgb_to_ansi(*wall_rgb, is_bg=True)
        # width: vertical: 1, horizontal: 3
        return f"{wall_bg} {reset}" if is_x_even else f"{wall_bg}   {reset}"

    # passages and rooms
    if is_x_even:
        # vertical passage
        return f"{cell_style} {reset}"

    if not is_y_even:
        # room
        if state == CellState.ENTRY:
            return f"{cell_style} S {reset}"
        if state == CellState.EXIT:
            return f"{cell_style} E {reset}"
        if state == CellState.LOCK:
            return f"{cell_style}[$]{reset}"
        if state == CellState.PATH:
            # Fallback dot path
            dot = " • " if has_utf8 else " o "
            return f"{cell_style}{dot}{reset}"
        return f"{cell_style}   {reset}"

    # passage 3 width
    if state == CellState.PATH:
        dot = " • " if has_utf8 else " o "
        return f"{cell_style}{dot}{reset}"
    return f"{cell_style}   {reset}"


def draw_menu(y_offset: int, ctrl: AppController) -> None:
    is_narrow = (ctrl.width < 12)
    line_controls = ctrl.get_hud_controls_text(is_narrow=is_narrow)

    hud_blocks = ctrl.get_unified_hud_blocks()
    formatted_parts = []

    for b in hud_blocks:
        raw_text = f"{b['label']}: {b['value']}"
        spec = b['width_spec']

        if b['is_highlighted']:
            formatted_parts.append(f"<{raw_text:<{spec - 2}}>")
        else:
            formatted_parts.append(f"<{raw_text:<{spec}}>")

    raw_info = " | ".join(formatted_parts)

    reset = "\033[0m"
    color_edit = "\033[1;33m"
    color_seed = "\033[1;31m"

    if ctrl.is_entering_seed:
        info_colored = raw_info.replace("<", color_seed).replace(">", reset)
        line_controls = f"\033[1;31m{line_controls}{reset}"
    else:
        info_colored = raw_info.replace("<", color_edit).replace(">", reset)

    color_header = "\033[1:34m"

    # \033[?7l - Disable line wrapping
    # \033[?7h - Enable line wrapping
    # \033[J   - ED (Erase in Display): Clear screen from cursor to end
    # \033[2K  - EL (Erase in Line): Clear entire current line

    menu = (
        f"\033[?7l"
        f"\033[{y_offset};1H\033[J\033[2K{color_header}===Menu==={reset}"
        f"\033[{y_offset + 1};1H\033[J\033[2K{line_controls}"
        f"\033[{y_offset + 2};1H\033[J\033[2K{info_colored}"
        f"\033[{y_offset + 4};1H\033[J\033[2K Choice? (press key): \033[K"
        f"\033[?7h"
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
