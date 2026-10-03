from typing import TYPE_CHECKING
from app.backends.base import GraphicBackend
from app.backends.mlx_image import MLXImage
from app.grid import RenderGrid, CellState
from app.keys import MLX_EVENT_DESTROY, MLX_MASK_NO_MASK, KEY_MAP
from mlx import Mlx  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from app.engine import AppController


class MlxBackend(GraphicBackend):
    def __init__(self) -> None:
        self.block_size = 20
        self.pixel_width = 0
        self.pixel_height = 0
        self.mlx: Mlx = Mlx()
        self.mlx_ptr = self.mlx.mlx_init()
        self.win_ptr = None
        self.image: MLXImage | None = None
        # image: writable memory view of the image raw pixels plus metadata

    def init_window(self, width: int, height: int, title: str) -> None:
        blocks_x = (width * 2) + 1
        blocks_y = (height * 2) + 1
        self.pixel_width = blocks_x * self.block_size
        self.pixel_height = blocks_y * self.block_size

    def _draw_pixel_block(self, gx: int, gy: int,
                          color: tuple[int, int, int]) -> None:
        if self.image is None:
            return

        start_x = gx * self.block_size
        start_y = gy * self.block_size
        r, g, b = color

        for y in range(start_y, start_y + self.block_size):
            for x in range(start_x, start_x + self.block_size):
                self.image.put_pixel(x, y, r, g, b)

    def render_frame(self, grid: RenderGrid) -> None:

        color_map = {
            CellState.WALL: (51, 34, 17),  # Brown
            CellState.FLOOR: (17, 17, 17),  # Black
            CellState.ENTRY: (0, 255, 0),  # Green
            CellState.EXIT: (255, 0, 0),  # Red
            CellState.PATH: (0, 255, 255),  # Cyan
        }

        for y in range(grid.grid_height):
            for x in range(grid.grid_width):
                state = grid.cells[y][x]
                color = color_map.get(state, color_map[CellState.WALL])
                self._draw_pixel_block(x, y, color)

        if self.win_ptr and self.image:
            self.mlx.mlx_put_image_to_window(self.mlx_ptr, self.win_ptr,
                                             self.image.img_ptr, 0, 0)

    def start_loop(self, controller: AppController) -> None:

        self.win_ptr = self.mlx.mlx_new_window(
            self.mlx_ptr, self.pixel_width, self.pixel_height, "A MLX"
        )

        self.image = MLXImage(self.mlx, self.mlx_ptr, self.pixel_width,
                              self.pixel_height)

        self.mlx.mlx_hook(self.win_ptr, MLX_EVENT_DESTROY,
                          MLX_MASK_NO_MASK,
                          lambda *args: controller.handle_action("quit"), 0)

        def handle_mlx_keys(keycode: int, param: any = None) -> None:
            action = KEY_MAP.get(keycode)
            if action:
                controller.handle_action(action)

        self.mlx.mlx_key_hook(self.win_ptr, handle_mlx_keys, None)

        def loop_tick(param) -> None:
            if controller.is_running:
                controller.tick()
                self.render_frame(controller.grid)
            else:
                import sys
                sys.exit(0)

        self.mlx.mlx_loop_hook(self.mlx_ptr, loop_tick, None)
        self.mlx.mlx_loop(self.mlx_ptr)
