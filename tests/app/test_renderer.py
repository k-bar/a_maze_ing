import pytest
from app.backends.terminal import TerminalBackend


def test_should_clear_walls_in_buffer_for_specific_cell() -> None:
    width, height = 3, 3
    backend = TerminalBackend()
    backend.init_window(width, height, "Test Renderer")
    all_open_mask = 0

    backend.update_cell_in_buffer(x=1, y=1, wall_mask=all_open_mask)

    bx, by = 3, 3
    assert backend.buffer[by][bx] == " "  # Open Center
    assert backend.buffer[by - 1][bx] == " "  # Open N wall
    assert backend.buffer[by][bx + 1] == " "  # Open E wall
    assert backend.buffer[by + 1][bx] == " "  # Open S wall
    assert backend.buffer[by][bx - 1] == " "  # Open W wall
