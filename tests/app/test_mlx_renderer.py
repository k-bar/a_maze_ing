from app.backends.mlx import MlxBackend


def test_mlx_backend_should_calculate_correct_pixel_dimensions() -> None:
    width, height = 10, 10
    backend = MlxBackend()

    backend.init_window(width, height, "A Maze test")
    expected_pixel_width = ((width * 2) + 1) * 20
    expected_pixel_height = ((height * 2) + 1) * 20

    assert backend.pixel_width == expected_pixel_width
    assert backend.pixel_height == expected_pixel_height
