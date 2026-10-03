from app.grid import RenderGrid, CellState


def test_should_initialize_grid_with_walls() -> None:
    grid = RenderGrid(width=3, height=3)
    assert grid.grid_height == 7
    assert grid.grid_width == 7
    assert grid.cells[1][1] == CellState.WALL


def test_should_set_char_at_coordinates() -> None:
    grid = RenderGrid(width=3, height=3)
    grid.set_cell(x=1, y=1, state=CellState.FLOOR)
    assert grid.cells[1][1] == CellState.FLOOR
