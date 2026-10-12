from app.engine import AppController
from app.backends.base import GraphicBackend
from app.backends.mlx_image import MLXImage
from app.grid import RenderGrid, CellState
from app.keys import MLX_EVENT_DESTROY, MLX_MASK_NO_MASK, KEY_MAP
from mlx import Mlx


class MlxBackend(GraphicBackend):
    def __init__(self) -> None:
        self.block_size = 30
        self.wall_size: int = int(self.block_size / 10)
        self.pixel_width = 0
        self.pixel_height = 0
        self.mlx: Mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        self.image: MLXImage | None = None
        # image: writable memory view of the image raw pixels plus metadata

    def init_window(self, width: int, height: int, title: str) -> None:
        blocks_x = width
        blocks_y = height
        walls_x = width + 1
        walls_y = height + 1
        self.pixel_width = ((blocks_x * self.block_size)
                            + (walls_x * self.wall_size))
        self.pixel_height = ((blocks_y * self.block_size)
                             + (walls_y * self.wall_size))
        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.pixel_width, self.pixel_height, "A MLX"
        )
        self.image = MLXImage(self.mlx, self.mlx_ptr, self.pixel_width,
                              self.pixel_height)

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

        for y in range(start_y, start_y + size_y):
            for x in range(start_x, start_x + size_x):
                self.image.put_pixel(x, y, r, g, b)

    def _draw_path_block(self, gx: int, gy: int,
                         color: tuple[int, int, int]) -> None:
        if self.image is None:
            return

        if gx % 2 != 0 and gy % 2 != 0:
            start_x = ((((gx // 2) * self.block_size)
                       + (((gx // 2) + (gx % 2)) * self.wall_size))
                       + self.block_size // 3)

            start_y = ((((gy // 2) * self.block_size)
                       + (((gy // 2) + (gy % 2)) * self.wall_size))
                       + self.block_size // 3)


            size_y = self.block_size // 3
            size_x = self.block_size // 3

            r, g, b = color


        elif gx % 2 == 0 and gy % 2 != 0:
            start_x = ((((gx // 2) * self.block_size)
                       + (((gx // 2) + (gx % 2)) * self.wall_size))
                       - self.block_size // 2)

            start_y = ((((gy // 2) * self.block_size)
                       + (((gy // 2) + (gy % 2)) * self.wall_size))
                       + self.block_size // 3)

            size_y = self.block_size // 3
            size_x = self.wall_size + self.block_size

            r, g, b = color

        elif gx % 2 != 0 and gy % 2 == 0:
            start_x = (((gx // 2) * self.block_size)
                       + (((gx // 2) + (
                            gx % 2)) * self.wall_size)) + self.block_size // 3

            start_y = (((gy // 2) * self.block_size)
                       + (((gy // 2) + (
                            gy % 2)) * self.wall_size)) - self.block_size // 2

            size_y = self.wall_size + self.block_size
            size_x = self.block_size // 3

            r, g, b = color

        for y in range(start_y, start_y + size_y):
            for x in range(start_x, start_x + size_x):
                self.image.put_pixel(x, y, r, g, b)

    def render_frame(self, grid: RenderGrid) -> None:

        # color_map = {
        #     CellState.WALL: (128, 81, 37),  # Brown
        #     CellState.FLOOR: (30, 30, 30),  # Black
        #     CellState.ENTRY: (0, 255, 0),  # Green
        #     CellState.EXIT: (255, 0, 0),  # Red
        #     CellState.PATH: (0, 255, 255),  # Cyan
        #     CellState.LOCK: (222, 217, 213)
        # }
        color_map = {  # neutral
            CellState.WALL: (38, 50, 56),  # graphite
            CellState.FLOOR: (240, 233, 221),  # light
            CellState.ENTRY: (0, 137, 123),  # ocean
            CellState.EXIT: (230, 74, 25),  # orange
            CellState.PATH: (21, 101, 192),  # blue
            CellState.LOCK: (249, 168, 37),  # gold
        }

        while grid.changed:
            x, y, state = grid.changed.popleft()
            if state == CellState.PATH:
                color = color_map.get(state, color_map[CellState.WALL])
                self._draw_path_block(x, y, color)
            else:

                color = color_map.get(state, color_map[CellState.WALL])
                self._draw_pixel_block(x, y, color)

        if self.win_ptr and self.image:
            self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                             self.image.img_ptr, 0, 0)

    def start_loop(self, controller: AppController) -> None:
        self.mlx.mlx_hook(self.win_ptr, MLX_EVENT_DESTROY,
                          MLX_MASK_NO_MASK,
                          lambda *args: controller.handle_action("quit"), 0)

        def handle_mlx_keys(keycode: int, param: None = None) -> None:
            action = KEY_MAP.get(keycode)
            if action:
                controller.handle_action(action)

        self.mlx.mlx_key_hook(self.win_ptr, handle_mlx_keys, None)

        def loop_tick(param: None = None) -> None:
            if controller.is_running:
                controller.tick()
                self.render_frame(controller.grid)
            else:
                self.mlx.mlx_loop_exit(self.mlx_ptr)

        self.mlx.mlx_loop_hook(self.mlx_ptr, loop_tick, None)
        self.mlx.mlx_loop(self.mlx_ptr)
