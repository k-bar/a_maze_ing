import re
import subprocess

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from app.backends.palette import MazePalette, PRESETS
from app.engine import AppController
from app.backends.base import GraphicBackend
from app.backends.mlx_image import MLXImage
from app.grid import RenderGrid, CellState
from app.keys import MLX_EVENT_DESTROY, MLX_MASK_NO_MASK, KEY_MAP
from mlx import Mlx


class MlxBackend(GraphicBackend):
    def __init__(self) -> None:

        self.pixel_width = 0
        self.pixel_height = 0
        self.mlx: Mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        # image: writable memory view of the image raw pixels plus metadata
        self.image: MLXImage | None = None
        self.hud_image: MLXImage | None = None
        self.palette: MazePalette = PRESETS[0]
        self.preset_mode = 0

        self.fixed_win_width = 1280
        self.fixed_win_height = 720
        self.hud_height = 60
        self.maze_image_height = self.fixed_win_height - self.hud_height

        self.block_size = 30
        self.wall_size: int = int(self.block_size / 10)
        self.offset_x = 0
        self.offset_y = 0

        self.last_hud_state: str = ""
        self.controller: AppController | None = None

        self.init_frames_counter = 0
        self.keys_pressed: dict[int, bool] = {}
        self.key_repeat_cooldown = 0

    def init_window(self, width: int, height: int, title: str) -> None:

        self.block_size, self.wall_size, self.offset_x, self.offset_y = \
            calculate_mlx_geometry(
                maze_w=width,
                maze_h=height,
                win_w=self.fixed_win_width,
                win_h=self.fixed_win_height,
                hud_h=self.hud_height + 20
            )

        blocks_x = width
        blocks_y = height
        walls_x = width + 1
        walls_y = height + 1
        self.pixel_width = ((blocks_x * self.block_size)
                            + (walls_x * self.wall_size))
        self.pixel_height = ((blocks_y * self.block_size)
                             + (walls_y * self.wall_size))

        available_h = self.fixed_win_height - self.hud_height
        self.max_width = (self.fixed_win_width - 1) // 4
        self.max_height = (available_h - 1) // 4

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.fixed_win_width, self.fixed_win_height, title
        )
        self.maze_image_height = self.fixed_win_height - self.hud_height
        self.image = MLXImage(self.mlx, self.mlx_ptr, self.fixed_win_width,
                              self.maze_image_height)
        self.hud_image = MLXImage(self.mlx, self.mlx_ptr, self.fixed_win_width,
                                  self.hud_height)
        assert self.image is not None
        self.image.pixels[:, :] = [0, 0, 0, 255]

    def _draw_pixel_block(self, gx: int, gy: int,
                          color: tuple[int, int, int]) -> None:
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
        if self.image is None:
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

        current_palette = self.palette
        while grid.changed:
            x, y, state = grid.changed.popleft()
            if state == CellState.PATH:
                color = current_palette.get_rgb(state)
                self._draw_path_block(x, y, color)
            else:

                color = current_palette.get_rgb(state)
                self._draw_pixel_block(x, y, color)

        if self.win_ptr and self.image:
            assert self.controller is not None

            self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                             self.image.img_ptr, 0, 0)

            ctrl = self.controller
            current_hud_snapshot = (f"{ctrl.current_seed}_"
                                    f"{ctrl.is_entering_seed}_"
                                    f"{ctrl.seed_input_buffer}_"
                                    f"{ctrl.algorithm_name}_"
                                    f"{ctrl.solver_name}_"
                                    f"{ctrl.arrow_mode.name}_"
                                    f"{ctrl.width}_{ctrl.height}_"
                                    f"{ctrl.state.name}"
                                    f"{ctrl.steps_per_tick}")

            if (current_hud_snapshot != self.last_hud_state
                    or self.init_frames_counter < 2):

                if self.init_frames_counter < 5:
                    self.init_frames_counter += 1
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

                hud_top = self.fixed_win_height - self.hud_height

                assert self.hud_image is not None
                self.hud_image.pixels[hud_top:, :] = [0, 0, 0, 255]
                self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                                 self.hud_image.img_ptr, 0,
                                                 hud_top)

                hud_blocks = ctrl.get_unified_hud_blocks()
                x_positions = [20, 150, 380, 530, 690, 860, 1100]

                color_default = (170, 170, 170, 255)  # Grey
                color_seed = (255, 85, 85, 255)  # Red
                color_edit = (255, 204, 0, 255)  # Gold

                for i, block in enumerate(hud_blocks):
                    if i >= len(x_positions):
                        break

                    color = (
                        color_seed if block["is_seed"] else color_edit) \
                        if block["is_highlighted"] else color_default

                    full_text = f"{block['label']}: {block['value']}"
                    draw.text((x_positions[i], 10), full_text, fill=color,
                              font=font)

                controls_text = ctrl.get_hud_controls_text(is_narrow=False)
                c_color = color_seed \
                    if ctrl.is_entering_seed else color_default
                draw.text((20, 32), controls_text, fill=c_color, font=font)

                np_img = np.array(pil_img)

                bgra_img = np_img.copy()
                bgra_img[:, :, 0] = np_img[:, :, 2]  # B <- R
                bgra_img[:, :, 2] = np_img[:, :, 0]  # R <- B

                assert self.hud_image is not None
                self.hud_image.pixels[:, :] = bgra_img

                hud_top = self.fixed_win_height - self.hud_height
                self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                                 self.hud_image.img_ptr, 0,
                                                 hud_top)
            else:
                hud_top = self.fixed_win_height - self.hud_height
                assert self.hud_image is not None
                self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                                 self.hud_image.img_ptr, 0,
                                                 hud_top)

    def start_loop(self, controller: AppController) -> None:
        self.controller = controller
        self.mlx.mlx_hook(self.win_ptr, MLX_EVENT_DESTROY,
                          MLX_MASK_NO_MASK,
                          lambda *args: controller.handle_action("quit"),
                          0)

        def handle_press(keycode: int, param: None = None) -> None:

            self.keys_pressed[keycode] = True

            action = KEY_MAP.get(keycode)
            if action == "cycle_palette":
                self.change_colors(controller)
                return
            if action:
                is_repeatable = (
                        action.startswith("move_") or
                        action.startswith("digit_") or
                        action.startswith("seed_digit_") or
                        action == "seed_backspace"
                )
                if not is_repeatable:
                    controller.handle_action(action)
                    self.render_frame(controller.grid)

        def handle_release(keycode: int, param: None = None) -> None:

            if keycode in self.keys_pressed:
                self.keys_pressed[keycode] = False

        self.mlx.mlx_hook(self.win_ptr, 2, 1, handle_press, None)
        self.mlx.mlx_hook(self.win_ptr, 3, 2, handle_release, None)

        def loop_tick(param: None = None) -> None:
            if controller.is_running:
                if self.key_repeat_cooldown <= 0:
                    for k_code, is_pressed in self.keys_pressed.items():
                        if is_pressed:
                            act = KEY_MAP.get(k_code)
                            if act and (
                                    act.startswith("move_")
                                    or act.startswith("seed_digit_")
                                    or act.startswith("digit_")
                                    or act == "seed_backspace"):
                                controller.handle_action(act)
                                self.render_frame(controller.grid)

                    self.key_repeat_cooldown = 5
                else:
                    self.key_repeat_cooldown -= 1
                controller.tick()
                self.render_frame(controller.grid)
            else:
                self.mlx.mlx_loop_exit(self.mlx_ptr)

        self.mlx.mlx_loop_hook(self.mlx_ptr, loop_tick, None)
        self.mlx.mlx_loop(self.mlx_ptr)

    def change_colors(self, controller: AppController) -> None:

        old_palette = self.palette
        self.preset_mode = (self.preset_mode + 1) % 5
        if self.preset_mode < len(PRESETS):
            self.palette = PRESETS[self.preset_mode]
        else:
            self.palette = MazePalette.generate_random_harmonized()

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
        self.block_size, self.wall_size, self.offset_x, self.offset_y = \
            calculate_mlx_geometry(
                maze_w=width,
                maze_h=height,
                win_w=self.fixed_win_width,
                win_h=self.fixed_win_height,
                hud_h=self.hud_height + 20
            )
        if self.image is not None:
            self.image.pixels[:, :] = [0, 0, 0, 255]
        if self.hud_image is not None:
            self.hud_image.pixels[:, :] = [0, 0, 0, 255]

        self.last_hud_state = ""


def get_screen_resolution(fallback: tuple[int, int] = (1280, 720)) \
        -> tuple[int, int]:
    try:
        output = subprocess.check_output(
            "xrandr 2>dev/null | grep 'current'",
            shell=True,
            text=True
        )
        match = re.search(r"current\s+(\d+)\s*x\s*(\d+)", output)
        if match:
            return int(match.group(1)), int(match.group(2))
    except (subprocess.SubprocessError, FileNotFoundError, AttributeError):
        pass
    return fallback


def calculate_mlx_geometry(maze_w: int = 10, maze_h: int = 10,
                           win_w: int = 1280, win_h: int = 720,
                           hud_h: int = 60) -> tuple[int, int, int, int]:
    safety_margin = 10
    available_h = win_h - hud_h - safety_margin

    wall_size = 2

    required_walls_w = (maze_w + 1) * wall_size
    required_walls_h = (maze_h + 1) * wall_size

    if required_walls_w > win_w or required_walls_h > available_h:
        wall_size = 1

    remaining_w = win_w - ((maze_w + 1) * wall_size)
    remaining_h = available_h - ((maze_h + 1) * wall_size)

    max_block_w = remaining_w // maze_w
    max_block_h = remaining_h // maze_h

    block_size = min(max_block_w, max_block_h)
    if block_size < 1:
        block_size = 1
    if block_size > 1 and block_size % 2 == 0:
        block_size -= 1

    rendered_w = (maze_w * block_size) + ((maze_w + 1) * wall_size)
    rendered_h = (maze_h * block_size) + ((maze_h + 1) * wall_size)

    offset_x = (win_w - rendered_w) // 2
    offset_y = (available_h - rendered_h) // 2
    return block_size, wall_size, offset_x, offset_y
