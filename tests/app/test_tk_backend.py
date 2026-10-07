from types import SimpleNamespace
from unittest.mock import ANY, Mock

from app.backends.tk import TkBackend
from app.grid import RenderGrid


def test_tk_backend_renders_each_grid_cell() -> None:
    backend = TkBackend()
    backend.canvas = Mock()
    grid = RenderGrid(2, 2, (0, 0), (1, 1))

    backend.render_frame(grid)

    assert backend.canvas.create_rectangle.call_count == (
        grid.grid_width * grid.grid_height
    )
    coordinates = [
        call.args[:4]
        for call in backend.canvas.create_rectangle.call_args_list
    ]
    assert [coordinates[index] for index in (0, 1, 5, 6)] == [
        (0, 0, 2, 2),
        (3, 0, 32, 2),
        (0, 3, 2, 32),
        (3, 3, 32, 32),
    ]


def test_tk_backend_sizes_window_like_mlx(monkeypatch) -> None:
    root = Mock()
    canvas = Mock()
    monkeypatch.setattr("app.backends.tk.tk.Tk", lambda: root)
    monkeypatch.setattr(
        "app.backends.tk.tk.Canvas", lambda *args, **kwargs: canvas
    )

    backend = TkBackend()
    backend.init_window(2, 3, "Test")

    assert backend.canvas is canvas
    assert backend.root is root


def test_tk_backend_maps_keys_and_window_close_to_actions() -> None:
    backend = TkBackend()
    backend.root = Mock()
    backend.canvas = Mock()
    controller = Mock()
    controller.is_running = True
    controller.grid = RenderGrid(2, 2, (0, 0), (1, 1))

    backend.start_loop(controller)

    key_handler = backend.root.bind.call_args.args[1]
    key_handler(SimpleNamespace(keysym="1"))
    controller.handle_action.assert_called_once_with("regen")

    close_handler = backend.root.protocol.call_args.args[1]
    close_handler()
    controller.handle_action.assert_called_with("quit")
    backend.root.quit.assert_called_once()
    backend.root.mainloop.assert_called_once()
    assert backend.root.after.call_args_list[0].args == (0, ANY)
