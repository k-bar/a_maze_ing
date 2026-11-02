from app.backends.mlx import calculate_mlx_geometry


def test_calculate_mlx_geometry_small_maze() -> None:
    block_size, wall_size, offset_x, offset_y = calculate_mlx_geometry(
        maze_w=10, maze_h=10, win_w=1280, win_h=720, hud_h=60
    )

    assert block_size % 2 != 0
    assert wall_size >= 1

    rendered_w = (10 * block_size) + (11 * wall_size)
    rendered_h = (10 * block_size) + (11 * wall_size)

    assert rendered_w + offset_x * 2 <= 1280
    assert rendered_h + offset_y * 2 <= 720 - 60
    assert offset_x > 0
    assert offset_y > 0


def test_calculate_mlx_geometry_wide_maze() -> None:
    block_size, wall_size, offset_x, offset_y = calculate_mlx_geometry(
        maze_w=100, maze_h=10, win_w=1280, win_h=720, hud_h=60
    )

    rendered_w = (100 * block_size) + (101 * wall_size)
    rendered_h = (10 * block_size) + (11 * wall_size)

    assert rendered_w <= 1280
    assert rendered_h <= 720 - 60
