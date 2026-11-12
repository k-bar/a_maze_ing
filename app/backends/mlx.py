import itertools
import re
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.backends.palette import MazePalette, PRESETS
from app.engine import AppController, ArrowMode
from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.keys import MLX_EVENT_DESTROY, MLX_MASK_NO_MASK, KEY_MAP, \
    MLX_EVENT_CLIENT_MESSAGE
from mlx import Mlx
from mazegen import Direction


class MLXImage:
    """
    Wrapper for raw image buffer for MiniLibX.

    Provides a convenient interface to modify MiniLibX image pixels using
    a NumPy array for fast memory operations.
    """

    def __init__(self,
                 mlx: Mlx,
                 mlx_ptr: object,
                 width: int,
                 height: int) -> None:
        """
        Initializes a new MLX image buffer.

        Args:
            mlx: The MiniLibX instance.
            mlx_ptr: The MiniLibX context pointer.
            width: The width of the image in pixels.
            height: The height of the image in pixels.
        """
        self.img_ptr = mlx.mlx_new_image(mlx_ptr, width, height)
        img_info = mlx.mlx_get_data_addr(self.img_ptr)
        self.img_buffer: bytearray = img_info[0]
        self.bits_per_pixel: int = img_info[1]
        self.size_line: int = img_info[2]
        self.endian: int = img_info[3]
        raw_pixels = np.frombuffer(self.img_buffer, dtype=np.uint8).reshape(
            height, self.size_line // 4, 4
        )
        self.pixels = raw_pixels[:, :width]
        self.pixels.flags.writeable = True


class MlxBackend(GraphicBackend):
    """
    MiniLibX implementation of the GraphicBackend.

    Handles window creation, drawing operations, HUD rendering, and event
    loop management for the maze generator using the MLX library.
    """
    def __init__(self) -> None:
        """Initializes the MLX backend with default configurations."""
        super().__init__()

        self.pixel_width = 0
        self.pixel_height = 0
        self.mlx: Mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        # image: writable memory view of the image raw pixels plus metadata
        self.image: MLXImage | None = None
        self.hud_image: MLXImage | None = None
        self.palette: MazePalette = PRESETS[0]
        self._palette_stream = itertools.chain(
            PRESETS[1:],
            iter(MazePalette.generate_random_harmonized, None),
        )

        self.preset_mode = 0

        self.fixed_win_width = 1280
        self.fixed_win_height = 720
        self.hud_height = 60
        self.maze_image_height = self.fixed_win_height - self.hud_height

        self.block_size = 30
        self.block_min_size = 1
        self.wall_min_size = 1
        self.wall_size: int = int(self.block_size / 10)
        self.offset_x = 0
        self.offset_y = 0

        self.last_hud_state: str = ""
        self.controller: AppController | None = None

        self.init_frames_counter = 0
        self.keys_pressed: dict[int, bool] = {}
        self.key_repeat_cooldown = 0
        self.is_resizing = False

    def init_window(self, width: int, height: int, title: str) -> None:
        """
        Creates the application window and calculates layout geometry.

        Args:
            width: Number of maze cells horizontally.
            height: Number of maze cells vertically.
            title: Title of the window.
        """

        assert self.controller is not None
        cfg = self.controller.config

        if cfg.WINDOW_WIDTH and cfg.WINDOW_HEIGHT:
            self.fixed_win_width = cfg.WINDOW_WIDTH
            self.fixed_win_height = cfg.WINDOW_HEIGHT
        else:
            scr_w, scr_h = get_screen_resolution(fallback=(1280, 720))
            if scr_w > 1280 and scr_h > 720:
                self.fixed_win_width = int(scr_w * 0.9)
                self.fixed_win_height = int(scr_h * 0.9)
            else:
                self.fixed_win_width = 1280
                self.fixed_win_height = 720

        self.maze_image_height = self.fixed_win_height - self.hud_height

        self.block_size, self.wall_size, self.offset_x, self.offset_y = \
            calculate_mlx_geometry(
                block_min_size=self.block_min_size,
                maze_w=width,
                maze_h=height,
                win_w=self.fixed_win_width,
                win_h=self.fixed_win_height,
                hud_h=self.hud_height
            )

        available_h = self.fixed_win_height - self.hud_height

        self.controller.max_width = (self.fixed_win_width - 1) // (
                self.block_min_size + self.wall_min_size)
        self.controller.max_height = (available_h - 1) // (
                self.block_min_size + self.wall_min_size)

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.fixed_win_width, self.fixed_win_height, title
        )
        self.image = MLXImage(self.mlx, self.mlx_ptr, self.fixed_win_width,
                              self.maze_image_height)
        self.hud_image = MLXImage(self.mlx, self.mlx_ptr, self.fixed_win_width,
                                  self.hud_height)
        assert self.image is not None
        self.image.pixels[:, :] = [0, 0, 0, 255]
        self.mlx.mlx_do_key_autorepeatoff(self.mlx_ptr)

    def _draw_pixel_block(self, gx: int, gy: int,
                          color: tuple[int, int, int]) -> None:
        """
        Draws a rectangular block (wall or cell) based on grid coordinates.

        Args:
            gx: Grid X coordinate. Even values indicate walls, odd indicate
            cells.
            gy: Grid Y coordinate. Even values indicate walls, odd indicate
            cells.
            color: RGB tuple for the block color.
        """
        if self.image is None:
            return

        if gx % 2 == 0:
            start_x = (((gx // 2) * self.block_size)
                       + ((gx // 2) * self.wall_size))
            size_x = self.wall_size
        else:

            start_x = (((gx // 2) * self.block_size)
                       + (((gx // 2) + (gx % 2)) * self.wall_size))
            size_x = self.block_size

        if gy % 2 == 0:
            start_y = (((gy // 2) * self.wall_size)
                       + ((gy // 2) * self.block_size))
            size_y = self.wall_size
        else:
            start_y = (((gy // 2) * self.block_size)
                       + (((gy // 2) + (gy % 2)) * self.wall_size))
            size_y = self.block_size

        r, g, b = color

        real_start_x = start_x + self.offset_x
        real_start_y = start_y + self.offset_y

        self.image.pixels[
            real_start_y: real_start_y + size_y,
            real_start_x: real_start_x + size_x] = [b, g, r, 255]

    def _draw_path_block(self, gx: int, gy: int,
                         color: tuple[int, int, int]) -> None:
        """
        Draws a partial-width path connecting cells
        (used for solutions/generation).

        Args:
            gx: Grid X coordinate.
            gy: Grid Y coordinate.
            color: RGB tuple for the path color.
        """
        if self.image is None:
            return

        if self.block_size == 1:
            self._draw_pixel_block(gx, gy, color)
            return

        path_line_size = self.block_size // 3
        if path_line_size < 1:
            path_line_size = 1
        # ensure that parity of path is the same as cell
        if path_line_size > 1 and path_line_size % 2 == 0:
            path_line_size -= 1

        padding = (self.block_size - path_line_size) // 2

        # room
        if gx % 2 != 0 and gy % 2 != 0:
            start_x = ((((gx // 2) * self.block_size)
                        + (((gx // 2) + 1) * self.wall_size))
                       + padding)

            start_y = ((((gy // 2) * self.block_size)
                        + (((gy // 2) + 1) * self.wall_size))
                       + padding)

            size_y = path_line_size
            size_x = path_line_size

        # vertical wall
        elif gx % 2 == 0 and gy % 2 != 0:
            start_x = ((((gx // 2) * self.block_size)
                        + ((gx // 2) * self.wall_size)) - padding)

            start_y = ((((gy // 2) * self.block_size)
                        + (((gy // 2) + 1) * self.wall_size)) + padding)

            size_y = path_line_size
            size_x = self.wall_size + (padding * 2)

        # horizontal wall
        else:
            start_x = (((gx // 2) * self.block_size)
                       + (((gx // 2) + 1) * self.wall_size)) + padding

            start_y = (((gy // 2) * self.block_size)
                       + ((gy // 2) * self.wall_size)) - padding

            size_y = self.wall_size + (padding * 2)
            size_x = path_line_size

        r, g, b = color

        real_start_x = start_x + self.offset_x
        real_start_y = start_y + self.offset_y

        self.image.pixels[
            real_start_y: real_start_y + size_y,
            real_start_x: real_start_x + size_x] = [b, g, r, 255]

    def render_frame(self, grid: RenderGrid) -> None:
        """
        Updates the MLX image buffer with the current grid state and renders
        the HUD.

        Args:
            grid: RenderGrid containing the current logical state of the maze.
        """

        if not self.is_resizing:
            current_palette = self.palette

            if grid.require_full_redraw:
                grid.require_full_redraw = False
                grid.changed.clear()

                if self.image is not None:
                    self.image.pixels[:, :] = [0, 0, 0, 255]

                for y in range(grid.height * 2 + 1):
                    for x in range(grid.width * 2 + 1):
                        state = grid.cells[y, x]
                        color = current_palette.get_rgb(state)
                        self._draw_pixel_block(x, y, color)
            else:
                while grid.changed:
                    x, y, state = grid.changed.popleft()
                    if state == CellState.PATH:
                        color = current_palette.get_rgb(state)
                        self._draw_path_block(x, y, color)
                    else:
                        color = current_palette.get_rgb(state)
                        self._draw_pixel_block(x, y, color)

        else:
            assert self.controller is not None
            w = self.controller.width
            h = self.controller.height
            size_x = w * self.block_size + (w + 1) * self.wall_size
            size_y = h * self.block_size + (h + 1) * self.wall_size

            current_palette = self.palette
            r, g, b = current_palette.get_rgb(CellState.WALL)
            assert self.image is not None
            self.image.pixels[
                self.offset_y: self.offset_y + size_y,
                self.offset_x: self.offset_x + size_x] = [b, g, r, 255]

        if not (self.win_ptr and self.image):
            return
        self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                         self.image.img_ptr, 0, 0)

        assert self.controller is not None
        ctrl = self.controller
        current_hud_snapshot = (f"{ctrl.current_seed}_"
                                f"{ctrl.is_entering_seed}_"
                                f"{ctrl.seed_input_buffer}_"
                                f"{ctrl.algorithm_name}_"
                                f"{ctrl.config.PERFECT}"
                                f"{ctrl.solver_name}_"
                                f"{ctrl.arrow_mode.name}_"
                                f"{ctrl.width}_{ctrl.height}_"
                                f"{ctrl.state.name}"
                                f"{ctrl.steps_per_tick}")

        if current_hud_snapshot != self.last_hud_state:
            self.last_hud_state = current_hud_snapshot

            pil_img = Image.new("RGBA",
                                (self.fixed_win_width, self.hud_height),
                                (0, 0, 0, 255))
            draw = ImageDraw.Draw(pil_img)

            try:
                font = ImageFont.truetype(
                    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                    14)
            except IOError:
                font = ImageFont.load_default()

            hud_blocks = ctrl.get_unified_hud_blocks()

            usable_width = self.fixed_win_width - 80
            num_blocks = len(hud_blocks)

            step_x = usable_width // (
                    num_blocks - 1) if num_blocks > 1 else 150
            x_positions = [20 + (i * step_x) for i in range(num_blocks)]

            if len(x_positions) > 6:
                x_positions[6] = self.fixed_win_width - 140

            color_default = (170, 170, 170, 255)  # Grey
            color_seed = (255, 85, 85, 255)  # Red
            color_edit = (255, 204, 0, 255)  # Gold

            rendered_items = []
            total_text_width = 0

            for block in hud_blocks:
                color = (
                    color_seed if block["is_seed"] else color_edit) \
                    if block["is_highlighted"] else color_default

                full_text = f"{block['label']}: {block['value']}"
                text_w = int(draw.textlength(full_text, font=font))

                rendered_items.append((full_text, color, text_w))
                total_text_width += text_w

            margin_x = 20
            available_width = self.fixed_win_width - (2 * margin_x)
            num_blocks = len(rendered_items)

            if num_blocks > 1:
                gap = max(8, (available_width - total_text_width) / (
                        num_blocks - 1))
            else:
                gap = 0

            current_x = float(margin_x)
            for full_text, color, text_w in rendered_items:
                draw.text((int(current_x), 10), full_text, fill=color,
                          font=font)
                current_x += text_w + gap

            controls_text = ctrl.get_hud_controls_text(is_narrow=False)
            c_color = color_seed if ctrl.is_entering_seed else color_default
            draw.text((20, 32), controls_text, fill=c_color, font=font)

            np_img = np.array(pil_img)
            bgra_img = np_img.copy()
            bgra_img[:, :, 0] = np_img[:, :, 2]  # B <- R
            bgra_img[:, :, 2] = np_img[:, :, 0]  # R <- B

            hud_top = self.fixed_win_height - self.hud_height
            assert self.hud_image is not None
            self.hud_image.pixels[:, :] = bgra_img
            self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                             self.hud_image.img_ptr, 0,
                                             hud_top)

    def start_loop(self, controller: AppController) -> None:
        """
        Starts the MiniLibX event loop and registers key/window hooks.

        Args:
            controller: The main AppController handling application logic.
        """
        self.controller = controller

        def on_close(*args: object) -> None:
            controller.handle_action("quit")

        self.mlx.mlx_hook(
            self.win_ptr,
            MLX_EVENT_DESTROY,
            MLX_MASK_NO_MASK,
            on_close,
            0,
        )
        self.mlx.mlx_hook(
            self.win_ptr,
            MLX_EVENT_CLIENT_MESSAGE,
            MLX_MASK_NO_MASK,
            on_close,
            0,
        )

        def handle_press(keycode: int, param: None = None) -> None:
            try:
                action = KEY_MAP.get(keycode)
                if not action:
                    return

                if action == "cycle_palette":
                    self.change_colors()
                    return

                assert self.controller is not None
                if not action.startswith("move_"):
                    controller.handle_action(action)
                    return

                self.keys_pressed[keycode] = True
            except Exception as e:
                import logging
                logging.critical("Error inside MLX handle_press",
                                 exc_info=True)
                print(f"\n[MLX INPUT ERROR] {e}", file=sys.stderr)
                self._cleanup()

        def handle_release(keycode: int, param: None = None) -> None:

            if keycode in self.keys_pressed:
                self.keys_pressed[keycode] = False

        self.mlx.mlx_hook(self.win_ptr, 2, 1, handle_press, None)
        self.mlx.mlx_hook(self.win_ptr, 3, 2, handle_release, None)

        def loop_tick(param: None = None) -> None:
            try:

                assert self.controller is not None
                if not controller.is_running:
                    self._cleanup()
                    return

                if self.key_repeat_cooldown > 0:
                    self.key_repeat_cooldown -= 1

                active_move_act: str | None = None
                for k, pressed in self.keys_pressed.items():
                    if pressed:
                        act = KEY_MAP.get(k)
                        if act and act.startswith("move_"):
                            active_move_act = act
                            break

                any_arrow_pressed = active_move_act is not None
                if self.is_resizing and not any_arrow_pressed:
                    self.is_resizing = False
                    controller.handle_action("regen")

                if active_move_act and self.key_repeat_cooldown <= 0:
                    if self.controller.arrow_mode == ArrowMode.SIZE:
                        self.key_repeat_cooldown = 4
                        self.is_resizing = True
                        action_to_direction = {
                            "move_up": Direction.NORTH,
                            "move_down": Direction.SOUTH,
                            "move_right": Direction.EAST,
                            "move_left": Direction.WEST,
                        }
                        direction = action_to_direction.get(active_move_act)
                        if direction:
                            new_w = self.controller.width + direction.dx
                            new_h = self.controller.height - direction.dy
                            self.controller.validate_and_apply_dimensions(
                                new_w, new_h)
                        self.controller.maze_resize()
                    else:
                        self.key_repeat_cooldown = 6
                        controller.handle_action(active_move_act)
                else:
                    controller.tick()

                self.render_frame(controller.grid)
            except Exception as e:
                import logging
                logging.critical("Error inside MLX loop_tick", exc_info=True)
                print(f"\n[MLX ERROR] {e}", file=sys.stderr)
                self._cleanup()

        self.mlx.mlx_loop_hook(self.mlx_ptr, loop_tick, None)
        self.mlx.mlx_loop(self.mlx_ptr)

    def change_colors(self) -> None:
        """
        Cycles the color palette and dynamically updates existing image pixels
        without requiring a full maze redraw.
        """
        old_palette = self.palette
        self.palette = next(self._palette_stream)
        if self.image is None:
            return

        current_pixels = self.image.pixels
        for state in CellState:
            old_rgb = old_palette.get_rgb(state)
            new_rgb = self.palette.get_rgb(state)
            if old_rgb == new_rgb:
                continue
            old_bgr = [old_rgb[2], old_rgb[1], old_rgb[0], 255]
            new_bgr = [new_rgb[2], new_rgb[1], new_rgb[0], 255]
            mask = np.all(current_pixels == old_bgr, axis=-1)
            current_pixels[mask] = new_bgr

    def update_geometry(self, width: int, height: int) -> None:
        """
        Recalculates rendering constraints and sizes for a newly sized maze.

        Args:
            width: New horizontal maze dimension.
            height: New vertical maze dimension.
        """
        self.block_size, self.wall_size, self.offset_x, self.offset_y = \
            calculate_mlx_geometry(
                block_min_size=self.block_min_size,
                maze_w=width,
                maze_h=height,
                win_w=self.fixed_win_width,
                win_h=self.fixed_win_height,
                hud_h=self.hud_height
            )
        if self.image is not None:
            self.image.pixels[:, :] = [0, 0, 0, 255]
        self.last_hud_state = ""

    def _cleanup(self) -> None:
        """Safely restores X11 autorepeat and destroys MLX resources."""
        if self.mlx and self.mlx_ptr:
            try:
                self.mlx.mlx_do_key_autorepeaton(self.mlx_ptr)
            except Exception:
                pass
            if self.image is not None:
                self.mlx.mlx_destroy_image(self.mlx_ptr, self.image.img_ptr)
                self.image = None
            if self.hud_image is not None:
                self.mlx.mlx_destroy_image(self.mlx_ptr,
                                           self.hud_image.img_ptr)
                self.hud_image = None
            if self.win_ptr is not None:
                self.mlx.mlx_destroy_window(self.mlx_ptr, self.win_ptr)
                self.win_ptr = None
            self.mlx.mlx_loop_exit(self.mlx_ptr)


def get_screen_resolution(fallback: tuple[int, int] = (1280, 720)) \
        -> tuple[int, int]:
    """
    Retrieves the current display resolution using the `xrandr` shell command.

    Args:
        fallback: A fallback resolution tuple (width, height) used if the
                  command fails or the system does not support xrandr.

    Returns:
        tuple[int, int]: The screen resolution (width, height).
    """
    try:
        output = subprocess.check_output(
            "xrandr 2>/dev/null | grep 'current'",
            shell=True,
            text=True
        )
        match = re.search(r"current\s+(\d+)\s*x\s*(\d+)", output)
        if match:
            return int(match.group(1)), int(match.group(2))
    except (subprocess.SubprocessError, FileNotFoundError, AttributeError):
        pass
    return fallback


def calculate_mlx_geometry(block_min_size: int = 1, maze_w: int = 10,
                           maze_h: int = 10,
                           win_w: int = 1280, win_h: int = 720,
                           hud_h: int = 60) -> tuple[int, int, int, int]:
    """
    Calculates the optimum dimensions and offsets to center a maze inside
    a window.

    Determines the largest possible integer sizes for cells and walls so the
    maze
    uses as much available window space as possible without overflowing.

    Args:
        block_min_size: Minimum pixel size for a single maze cell.
        maze_w: Number of maze cells horizontally.
        maze_h: Number of maze cells vertically.
        win_w: Window width in pixels.
        win_h: Window total height in pixels.
        hud_h: Height reserved for the HUD at the bottom.

    Returns:
        tuple[int, int, int, int]: Computed values for:
            - block_size (width/height of a cell)
            - wall_size (thickness of walls)
            - offset_x (padding from left edge)
            - offset_y (padding from top edge)
    """
    available_h = win_h - hud_h

    max_possible_w = (win_w - (maze_w + 1)) // maze_w
    max_possible_h = (available_h - (maze_h + 1)) // maze_h
    absolute_max_block = min(max_possible_w, max_possible_h)

    if absolute_max_block <= block_min_size:
        wall_size = 1
        block_size = block_min_size
    elif absolute_max_block <= 5:
        wall_size = 1
        block_size = absolute_max_block
    elif absolute_max_block <= 10:
        wall_size = 2
        rem_w = win_w - ((maze_w + 1) * wall_size)
        rem_h = available_h - ((maze_h + 1) * wall_size)
        block_size = min(rem_w // maze_w, rem_h // maze_h)
    else:
        wall_size = max(3, absolute_max_block // 10)
        rem_w = win_w - ((maze_w + 1) * wall_size)
        rem_h = available_h - ((maze_h + 1) * wall_size)
        block_size = min(rem_w // maze_w, rem_h // maze_h)

    if block_size > block_min_size and block_size % 2 == 0:
        block_size -= 1

    if block_size <= block_min_size:
        block_size = block_min_size

    rendered_w = (maze_w * block_size) + ((maze_w + 1) * wall_size)
    rendered_h = (maze_h * block_size) + ((maze_h + 1) * wall_size)

    offset_x = (win_w - rendered_w) // 2
    offset_y = (available_h - rendered_h) // 2
    return block_size, wall_size, offset_x, offset_y
