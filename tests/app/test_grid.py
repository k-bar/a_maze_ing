from app.grid import RenderGrid, CellState


def test_should_initialize_grid_with_walls() -> None:
    grid = RenderGrid(width=3, height=3, m_entry=(0, 0), m_exit=(2, 2))
    assert grid.grid_height == 7
    assert grid.grid_width == 7
    assert grid.cells[0, 0] == CellState.WALL
    assert grid.cells[1, 1] == CellState.ENTRY
    assert grid.cells[5, 5] == CellState.EXIT
    assert grid.cells[2, 2] == CellState.WALL
    assert grid.cells[3, 3] == CellState.FLOOR
