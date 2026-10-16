from _pytest.monkeypatch import MonkeyPatch

from app.backends.mlx import MlxBackend


def test_mlx_backend_should_calculate_correct_pixel_dimensions(
        monkeypatch: MonkeyPatch) -> None:
    width, height = 15, 25
    backend = MlxBackend()

    block_size = 30
    wall_size = block_size // 10

    expected_pixel_width = (width * block_size) + (width + 1) * wall_size
    expected_pixel_height = (height * block_size) + (height + 1) * wall_size

    class FakeMLX:
        def mlx_init(self) -> str:
            return "fake_mlx_ptr"

        def mlx_new_window(self, mlx_ptr: str, w: int, h: int, title: str) \
                -> str:
            return "fake_win_ptr"

        def mlx_new_image(self, mlx_ptr: str, w: int, h: int) -> str:
            return "fake_img_ptr"

        def mlx_get_data_addr(self, img_ptr: str) \
                -> tuple[bytearray, int, int, int]:
            fake_buffer_size = expected_pixel_width * expected_pixel_height * 4
            fake_bytearray = bytearray(fake_buffer_size)
            size_line = expected_pixel_width * 4
            return fake_bytearray, 32, size_line, 0

    monkeypatch.setattr(backend, "mlx", FakeMLX())
    backend.init_window(width, height, "Monkey see, monkey do")

    assert backend.pixel_width == expected_pixel_width
    assert backend.pixel_height == expected_pixel_height
