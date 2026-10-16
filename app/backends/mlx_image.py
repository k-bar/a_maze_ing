import numpy as np
from mlx import Mlx


class MLXImage:
    """Wrapper for raw image buffer for MiniLibX"""

    def __init__(self,
                 mlx: Mlx,
                 mlx_ptr: object,
                 width: int,
                 height: int) -> None:
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

    def put_pixel(self, x: int, y: int, r: int, g: int, b: int) -> None:
        """puts pixels in BGRA format directly to RAM"""
        offset = (y * self.size_line) + (x * 4)
        if 0 <= offset < len(self.img_buffer) - 4:
            self.img_buffer[offset] = b
            self.img_buffer[offset + 1] = g
            self.img_buffer[offset + 2] = r
            self.img_buffer[offset + 3] = 255  # Alpha
