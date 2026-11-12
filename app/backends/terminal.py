"""
Terminal backend module for rendering mazes and handling user interaction.

This module provides the `TerminalBackend` class, which uses ANSI escape codes,
raw terminal mode (tty), and standard input/output streams to draw interactive
mazes directly in the console.
"""
import io
import os
import select
import sys
import threading
import time
import tty
import termios
from dataclasses import dataclass
from enum import Enum, auto
from queue import Empty, Queue
from typing import Any, Optional

import numpy as np

from app.backends.base import GraphicBackend
from app.backends.palette import MazePalette, PRESETS
from app.grid import RenderGrid, CellState
from app.engine import AppController

input_queue: Queue[str] = Queue()


class TerminalRenderMode(Enum):
    """
    Enumeration of available visual rendering modes for the terminal.
    """
    BOX_THIN = auto()
    BOX_HEAVY = auto()
    BOX_DOUBLE = auto()
    ASCII = auto()
    BLOCKS = auto()


@dataclass(frozen=True)
class BoxTileSet:
    """
    Defines the character set used for rendering box-drawing characters.

    Attributes:
        chars (dict[tuple[bool, bool, bool, bool], str]): Mapping of neighbor
            states (up, down, left, right) to the corresponding box character.
        horiz_fill (str): The character used to fill horizontal spaces between
        nodes.
    """
    chars: dict[tuple[bool, bool, bool, bool], str]
    horiz_fill: str


THIN_TILES = BoxTileSet(
    horiz_fill="─",
    chars={
        (False, False, False, False): " ",
        (True, True, False, False): "│",
        (False, False, True, True): "─",
        (False, True, False, True): "┌",
        (False, True, True, False): "┐",
        (True, False, False, True): "└",
        (True, False, True, False): "┘",
        (True, True, False, True): "├",
        (True, True, True, False): "┤",
        (False, True, True, True): "┬",
        (True, False, True, True): "┴",
        (True, True, True, True): "┼",
        (True, False, False, False): "│",
        (False, True, False, False): "│",
        (False, False, True, False): "─",
        (False, False, False, True): "─",
    },
)

HEAVY_TILES = BoxTileSet(
    horiz_fill="━",
    chars={
        (False, False, False, False): " ",
        (True, True, False, False): "┃",
        (False, False, True, True): "━",
        (False, True, False, True): "┏",
        (False, True, True, False): "┓",
        (True, False, False, True): "┗",
        (True, False, True, False): "┛",
        (True, True, False, True): "┣",
        (True, True, True, False): "┫",
        (False, True, True, True): "┳",
        (True, False, True, True): "┻",
        (True, True, True, True): "╋",
        (True, False, False, False): "┃",
        (False, True, False, False): "┃",
        (False, False, True, False): "━",
        (False, False, False, True): "━",
    },
)

DOUBLE_TILES = BoxTileSet(
    horiz_fill="═",
    chars={
        (False, False, False, False): "•",
        (True, True, False, False): "║",
        (False, False, True, True): "═",
        (False, True, False, True): "╔",
        (False, True, True, False): "╗",
        (True, False, False, True): "╚",
        (True, False, True, False): "╝",
        (True, True, False, True): "╠",
        (True, True, True, False): "╣",
        (False, True, True, True): "╦",
        (True, False, True, True): "╩",
        (True, True, True, True): "╬",
        (True, False, False, False): "║",
        (False, True, False, False): "║",
        (False, False, True, False): "═",
        (False, False, False, True): "═",
    },
)

BOX_MODE_PAIRS: dict[TerminalRenderMode, tuple[BoxTileSet, BoxTileSet]] = {
    TerminalRenderMode.BOX_THIN: (THIN_TILES, DOUBLE_TILES),
    TerminalRenderMode.BOX_HEAVY: (HEAVY_TILES, DOUBLE_TILES),
    TerminalRenderMode.BOX_DOUBLE: (DOUBLE_TILES, HEAVY_TILES),
}


class TerminalBackend(GraphicBackend):
    """
    Handles terminal-based rendering and interactive input listening.
    """
    def __init__(self) -> None:
        """Initializes the terminal backend state."""
        super().__init__()
        self._last_grid_w: int = 0
        self._last_grid_h: int = 0
        self.controller: AppController | None = None
        self.palette: MazePalette = PRESETS[0]
        self.preset_mode = 0
        self.render_mode: TerminalRenderMode = TerminalRenderMode.BOX_HEAVY

    def init_window(self, width: int, height: int, title: str) -> None:
        """
        No-op for the terminal backend, as the window is the terminal itself.
        """
        pass

    def render_frame(self, grid: RenderGrid) -> None:
        """
        Draws the current state of the grid to the terminal using ANSI escapes.

        Calculates delta updates to minimize console output bandwidth, and
        redraws the entire menu/grid only when dimensions change or a full
        redraw is explicitly requested.

        Args:
            grid (RenderGrid): The maze grid object containing cell states.
        """

        if grid.require_full_redraw:
            grid.require_full_redraw = False
            grid.push_entire_grid_to_changed()

        if grid.width != self._last_grid_w or grid.height != self._last_grid_h:
            self._last_grid_w = grid.width
            self._last_grid_h = grid.height
            _real_output.write("\033[2J\033[1;1H")
            _real_output.flush()

            menu_y_position = len(grid.cells) + 2
            assert self.controller is not None
            draw_menu(menu_y_position, self.controller)

        updates: dict[tuple[int, int], CellState] = {}
        while grid.changed:
            x, y, state = grid.changed.popleft()
            updates[(x, y)] = state

        if self.render_mode in BOX_MODE_PAIRS and updates:
            grid_h, grid_w = grid.cells.shape
            extra_neighbors: dict[tuple[int, int], CellState] = {}
            for (x, y) in updates:
                for dx, dy in ((0, -1), (0, 1), (-1, 0), (1, 0)):
                    nx, ny = x + dx, y + dy
                    if (0 <= nx < grid_w and 0 <= ny < grid_h
                            and (nx, ny) not in updates):
                        extra_neighbors[(nx, ny)] = grid.cells[ny, nx]
            updates.update(extra_neighbors)

        chunks: list[str] = []
        for (tx, ty), cell_st in updates.items():
            content = resolve_cell_content(
                tx, ty, cell_st, self.palette, grid.cells, self.render_mode
            )
            screen_x = (tx // 2 * 4) + (1 if tx % 2 != 0 else 0)
            chunks.append(f"\033[{ty + 1};{screen_x + 1}H{content}")

        if chunks:
            _real_output.write("".join(chunks))
            _real_output.flush()

    def change_colors(self, controller: "AppController") -> None:
        """
        Cycles through predefined color palettes or generates a random one.

        Args:
            controller (AppController): The main application controller.
        """

        self.preset_mode = (self.preset_mode + 1) % 5
        if self.preset_mode < len(PRESETS):
            self.palette = PRESETS[self.preset_mode]
        else:
            self.palette = MazePalette.generate_random_harmonized()
        controller.grid.require_full_redraw = True

    def cycle_render_mode(self, controller: AppController) -> None:
        """
        Cycles the active rendering style (e.g., ASCII, heavy boxes, blocks).

        Args:
            controller (AppController): The main application controller.
        """
        modes = list(TerminalRenderMode)
        next_idx = (modes.index(self.render_mode) + 1) % len(modes)
        self.render_mode = modes[next_idx]
        controller.grid.require_full_redraw = True

    def start_loop(self, controller: "AppController") -> None:
        """
        Initiates the main interactive terminal loop.

        Sets up the terminal in raw mode, spawns a daemon thread for reading
        asynchronous keyboard inputs, and loops over controller ticks.
        Restores the terminal to its original state upon exit.

        Args:
            controller (AppController): The application state controller.
        """
        if not sys.stdin.isatty() or not sys.stdout.isatty():
            print(
                "[TERMINAL ERROR] Application requires an "
                "interactive terminal (TTY).",
                file=sys.stderr
            )
            controller.is_running = False
            return

        self.controller = controller
        cols, lines = get_terminal_dimensions()
        calc_max_w = (cols - 1) // 4 - 1
        calc_max_h = (lines - 1 - 7) // 2

        if calc_max_w < 3 or calc_max_h < 3:
            print(
                f"[TERMINAL ERROR] Terminal window is too small "
                f"({cols}x{lines}). "
                f"Minimum required size is 17x15 characters.",
                file=sys.stderr
            )
            controller.is_running = False
            return

        controller.max_width = calc_max_w
        controller.max_height = calc_max_h

        if (controller.width > controller.max_width
                or controller.height > controller.max_height):
            controller.validate_and_apply_dimensions(controller.width,
                                                     controller.height)
            controller.handle_action("regen")

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
                        elif key_lowered == "t":
                            self.cycle_render_mode(controller)
                        elif pressed_key in ["\x1b[4~", "\x1b[F", "\x1b[OF"]:
                            controller.handle_action("skip")
                        elif pressed_key == '\r' or pressed_key == '\n':
                            controller.handle_action("enter_action")
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
        """Updates internal geometry logic. No-op for terminal."""
        pass


# global stash for terminal settings
_original_terminal_settings: Optional[list[Any]] = None
_real_output = sys.stdout
_devnull_stream = io.StringIO()


def setup_terminal() -> None:
    """
    Sets the terminal into raw mode and initializes alternative screen buffer.

    Disables local echo, hides the cursor, clears the screen, and buffers
    all output directly via sys.stdout while rerouting standard streams to
    avoid pollution from other print statements.
    """
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
    """
    Restores the terminal to its original canonical state.

    Disables the alternative screen buffer, shows the cursor, and re-attaches
    the standard output and error streams.
    """
    if _original_terminal_settings is not None:
        fd = sys.stdin.fileno()
        # termios.tcflush(fd, termios.TCIFLUSH)
        termios.tcsetattr(fd, termios.TCSAFLUSH, _original_terminal_settings)

        sys.stdout = _real_output
        sys.stderr = sys.__stderr__

        sys.stdout.write("\033[?1049l\033[?25h")
        sys.stdout.flush()


def input_thread_worker() -> None:
    """
    Background worker thread function that reads raw keystrokes from stdin.

    Handles standard characters as well as multi-byte ANSI escape sequences
    (such as arrow keys) and pushes them into a thread-safe queue.
    """
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
                    ch += b_rest.decode('utf-8', errors='ignore')

            input_queue.put(ch)
        except OSError:
            break


def supports_truecolor() -> bool:
    """
    Checks environment variables to determine if the terminal supports 24-bit
    TrueColor.

    Returns:
        bool: True if TrueColor is supported, False otherwise.
    """
    if os.environ.get("COLORTERM") in ("truecolor", "24bit"):
        return True
    if "TERM_PROGRAM" in os.environ:
        return True
    return False


def rgb_to_ansi(r: int, g: int, b: int, is_bg: bool = False) -> str:
    """
    Converts RGB values to an appropriate ANSI color escape sequence.

    Automatically falls back to a safe 16-color ANSI code if the terminal
    does not support TrueColor rendering.

    Args:
        r (int): Red channel (0-255).
        g (int): Green channel (0-255).
        b (int): Blue channel (0-255).
        is_bg (bool, optional): If True, returns a background color code.
        Defaults to False.

    Returns:
        str: The generated ANSI color escape sequence.
    """
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
    """
    Checks if the standard output stream supports UTF-8 encoding.

    Returns:
        bool: True if UTF-8 is supported, False otherwise.
    """
    try:
        return _real_output.encoding.lower() in ("utf-8", "utf8", "cp65001")
    except AttributeError:
        return False


def _get_connected_char(
        x: int,
        y: int,
        cells: np.ndarray[Any, Any],
        target_states: tuple[CellState, ...],
        tiles: BoxTileSet,
        has_utf8: bool,
) -> str:
    """
    Determines the appropriate box-drawing character based on neighbor cell
    states.

    Checks adjacent cells (up, down, left, right) and maps the connection
    pattern
    to a specific box-drawing character.

    Args:
        x (int): The X coordinate of the cell.
        y (int): The Y coordinate of the cell.
        cells (np.ndarray): The grid array containing cell states.
        target_states (tuple[CellState, ...]): The cell states to connect with.
        tiles (BoxTileSet): The tile set defining the characters.
        has_utf8 (bool): Flag indicating if UTF-8 is supported.

    Returns:
        str: The resolved character.
    """
    height, width = cells.shape
    up = (y > 0) and (cells[y - 1, x] in target_states)
    down = (y < height - 1) and (cells[y + 1, x] in target_states)
    left = (x > 0) and (cells[y, x - 1] in target_states)
    right = (x < width - 1) and (cells[y, x + 1] in target_states)

    neighbors = (up, down, left, right)
    if not has_utf8:
        return "+" if any(neighbors) else " "
    return tiles.chars.get(neighbors, "┼")


def _resolve_box_mode(
        x: int,
        y: int,
        state: CellState,
        palette: MazePalette,
        cells: np.ndarray[Any, Any],
        render_mode: TerminalRenderMode,
) -> str:
    """
    Resolves cell content when using a box-drawing rendering mode.
    """
    is_x_even = x % 2 == 0
    rgb = palette.get_rgb(state)
    reset = "\033[0m"
    cell_style = "\033[97m" if sum(rgb) < 120 else rgb_to_ansi(*rgb,
                                                               is_bg=False)
    has_utf8 = supports_utf8()

    wall_tiles, path_tiles = BOX_MODE_PAIRS[render_mode]

    if state == CellState.WALL:
        w_char = _get_connected_char(
            x, y, cells, (CellState.WALL,), wall_tiles, has_utf8
        )
        if is_x_even:
            return f"{cell_style}{w_char}{reset}"
        fill = wall_tiles.horiz_fill if has_utf8 else "-"
        char_mid = fill if w_char == wall_tiles.horiz_fill else w_char
        return f"{cell_style}{fill}{char_mid}{fill}{reset}"

    height, width = cells.shape
    path_states = (CellState.PATH, CellState.ENTRY, CellState.EXIT)
    left_path = (x > 0) and (cells[y, x - 1] in path_states)
    right_path = (x < width - 1) and (cells[y, x + 1] in path_states)
    p_fill = path_tiles.horiz_fill if has_utf8 else "-"

    if state in (CellState.ENTRY, CellState.EXIT):
        letter = "S" if state == CellState.ENTRY else "E"
        bg_ansi = rgb_to_ansi(*rgb, is_bg=True)
        fg_ansi = "\033[30m" if sum(rgb) // 3 > 128 else "\033[97m"
        badge_style = f"{bg_ansi}{fg_ansi}\033[1m"

        left_ch = f"{cell_style}{p_fill}{reset}" if left_path else " "
        right_ch = f"{cell_style}{p_fill}{reset}" if right_path else " "
        return f"{left_ch}{badge_style}{letter}{reset}{right_ch}"

    if state == CellState.LOCK:
        bg_ansi = rgb_to_ansi(*rgb, is_bg=True)
        fg_ansi = "\033[30m" if sum(rgb) // 3 > 128 else "\033[97m"
        fill_char = "░" if has_utf8 else "#"
        return f"{bg_ansi}{fg_ansi}{fill_char * 3}{reset}"

    if state == CellState.PATH:
        if not has_utf8:
            return f"{cell_style}o{reset}" \
                if is_x_even else f"{cell_style} o {reset}"
        p_char = _get_connected_char(
            x, y, cells, path_states, path_tiles, has_utf8
        )
        if is_x_even:
            return f"{cell_style}{p_char}{reset}"
        left_ch = p_fill if left_path else " "
        right_ch = p_fill if right_path else " "
        return f"{cell_style}{left_ch}{p_char}{right_ch}{reset}"

    return " " if is_x_even else "   "


def _resolve_blocks_mode(
        x: int, state: CellState, palette: MazePalette
) -> str:
    """
    Resolves cell content when using the solid block rendering mode.
    """
    is_x_even = x % 2 == 0
    rgb = palette.get_rgb(state)
    reset = "\033[0m"
    bg_ansi = rgb_to_ansi(*rgb, is_bg=True)
    text_color = "\033[30m" if sum(rgb) // 3 > 128 else "\033[37m"
    cell_style = f"{bg_ansi}{text_color}"

    if state == CellState.WALL:
        wall_rgb = palette.get_rgb(CellState.WALL)
        wall_bg = rgb_to_ansi(*wall_rgb, is_bg=True)
        return f"{wall_bg} {reset}" if is_x_even else f"{wall_bg}   {reset}"

    if is_x_even:
        return f"{cell_style} {reset}"

    if state == CellState.ENTRY:
        return f"{cell_style} S {reset}"
    if state == CellState.EXIT:
        return f"{cell_style} E {reset}"
    if state == CellState.LOCK:
        return f"{cell_style}[$]{reset}"
    if state == CellState.PATH:
        dot = " • " if supports_utf8() else " o "
        return f"{cell_style}{dot}{reset}"
    return f"{cell_style}   {reset}"


def _resolve_ascii_mode(
        x: int, y: int, state: CellState, palette: MazePalette
) -> str:
    """
    Resolves cell content when using a plain ASCII rendering mode.
    """
    is_x_even = x % 2 == 0
    is_y_even = y % 2 == 0
    rgb = palette.get_rgb(state)
    reset = "\033[0m"
    fg_style = "\033[97m" if sum(rgb) < 120 else rgb_to_ansi(*rgb, is_bg=False)
    has_utf8 = supports_utf8()

    if is_x_even and is_y_even:
        wall_rgb = palette.get_rgb(CellState.WALL)
        wall_fg = (
            "\033[97m"
            if sum(wall_rgb) < 120
            else rgb_to_ansi(*wall_rgb, is_bg=False)
        )
        return f"{wall_fg}+{reset}"

    if state == CellState.PATH:
        dot_single = "•" if has_utf8 else "o"
        if is_x_even:
            return f"{fg_style}{dot_single}{reset}"
        return f"{fg_style} {dot_single} {reset}"

    if is_x_even and not is_y_even:
        return f"{fg_style}|{reset}" if state == CellState.WALL else " "
    if not is_x_even and is_y_even:
        return f"{fg_style}---{reset}" if state == CellState.WALL else "   "

    if state in (CellState.ENTRY, CellState.EXIT):
        letter = "S" if state == CellState.ENTRY else "E"
        bg_ansi = rgb_to_ansi(*rgb, is_bg=True)
        fg_ansi = "\033[30m" if sum(rgb) // 3 > 128 else "\033[97m"
        return f" {bg_ansi}{fg_ansi}\033[1m{letter}{reset} "

    if state == CellState.LOCK:
        bg_ansi = rgb_to_ansi(*rgb, is_bg=True)
        fg_ansi = "\033[30m" if sum(rgb) // 3 > 128 else "\033[97m"
        return f"{bg_ansi}{fg_ansi}[$]{reset}"

    return "   "


def resolve_cell_content(
        x: int,
        y: int,
        state: CellState,
        palette: MazePalette,
        cells: np.ndarray[Any, Any],
        render_mode: TerminalRenderMode,
) -> str:
    """
    Determines the string content and ANSI styling for a single cell.

    Routes the calculation to the specific resolution function matching
    the current render mode.

    Args:
        x (int): The X coordinate.
        y (int): The Y coordinate.
        state (CellState): The cell's state enum.
        palette (MazePalette): The color palette used for rendering.
        cells (np.ndarray): The 2D array of all cells.
        render_mode (TerminalRenderMode): The active visual rendering mode.

    Returns:
        str: The stylized string representation of the cell.
    """
    if render_mode in BOX_MODE_PAIRS:
        return _resolve_box_mode(x, y, state, palette, cells, render_mode)
    if render_mode == TerminalRenderMode.ASCII:
        return _resolve_ascii_mode(x, y, state, palette)
    return _resolve_blocks_mode(x, state, palette)


def draw_menu(y_offset: int, ctrl: AppController) -> None:
    """
    Renders the interactive menu and HUD below the main maze view.

    Args:
        y_offset (int): The starting vertical line index for the menu.
        ctrl (AppController): The main application controller providing state
        logic.
    """
    is_narrow = (ctrl.width < 12)
    line_controls = ctrl.get_hud_controls_text(is_narrow=is_narrow)

    if not is_narrow and not ctrl.is_entering_seed:
        line_controls = line_controls.replace(
            "[C]olors", "[C]olors | [T]iles"
        )

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

    color_header = "\033[1;34m"

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
    """
    Retrieves the actual dimensions (columns, lines) of the terminal.

    Args:
        fallback (tuple[int, int], optional): Fallback size if OS call fails.

    Returns:
        tuple[int, int]: A tuple representing (columns, lines).
    """
    try:
        size = os.get_terminal_size()
        return size.columns, size.lines
    except OSError:
        return fallback
