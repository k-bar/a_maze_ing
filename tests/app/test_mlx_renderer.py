from _pytest.monkeypatch import MonkeyPatch

from app.backends.mlx import MlxBackend


def test_mlx_backend_should_calculate_correct_pixel_dimensions(
        monkeypatch: MonkeyPatch) -> None:
    width, height = 15, 25
    backend = MlxBackend()

    class FakeMLX:
        def mlx_init(self) -> None:
            pass

        def mlx_new_window(self, mlx_ptr: str, w: int, h: int) -> str:
            return "fake_win_ptr"

        def mlx_new_image(self, mlx_ptr: str, w: int) -> str:
            return "fake_img_ptr"

        def mlx_get_data_addr(self, mlx_pt: str) -> str:
            return "fake_addr_ptr"

    monkeypatch.setattr(backend, "mlx", FakeMLX)

    backend.init_window(width, height, "Monkey see, monkey do")

    block_size = 30
    wall_size = block_size / 10

    expected_pixel_width = (width * block_size) + (width + 1) * wall_size
    expected_pixel_height = (height * block_size) + (height + 1) * wall_size

    assert backend.pixel_width == expected_pixel_width
    assert backend.pixel_height == expected_pixel_height
