from unittest.mock import MagicMock

import pytest

from app import Config
from app.engine import AppController
from app.grid import CellState


@pytest.fixture
def default_config() -> Config:
    return Config(
        WIDTH=3,
        HEIGHT=3,
        ENTRY=(0, 0),
        EXIT=(2, 2),
        PERFECT=True,
        ALGORITHM="KRUSKAL",
        SEED=123
    )


def test_app_controller_should_initialize_correctly(
        default_config: Config) -> None:
    mock_backend = MagicMock()
    controller = AppController(default_config, backend=mock_backend)
    assert controller.width == 3
    assert controller.height == 3
    assert controller.algorithm_name == "KRUSKAL"


def test_controller_start_should_register_with_backend(
        default_config: Config) -> None:
    mock_backend = MagicMock()
    controller = AppController(default_config, backend=mock_backend)

    assert controller.is_running is True
    assert controller.is_generating is True

    # tests if method were called on mock with proper arguments
    controller.start()
    mock_backend.init_window.assert_called_once_with(3, 3, "A-Maze-ing")
    mock_backend.start_loop.assert_called_once_with(controller=controller)


def test_handle_action_regen_should_reset_generation_state(
        default_config: Config) -> None:
    backend = MagicMock()
    controller = AppController(default_config, backend=backend)

    controller.is_generating = False

    assert controller.is_generating is False
    controller.handle_action("regen")
    assert controller.is_generating is True


def test_handle_action_quit_should_stop_the_engine(
        default_config: Config) -> None:
    mock_backend = MagicMock()
    controller = AppController(default_config, backend=mock_backend)

    assert controller.is_running is True
    controller.handle_action("quit")
    assert controller.is_running is False


def test_should_destroy_only_the_physical_wall_tile(
        default_config: Config) -> None:
    class MockDirection:
        dy = 0
        dx = 1

    mock_backend = MagicMock()
    controller = AppController(default_config, backend=mock_backend)

    controller.generator = MagicMock()
    controller.generator.step.return_value = (0, 0, MockDirection())

    assert controller.grid.cells[1][2] == CellState.WALL
    controller.tick()
    assert controller.grid.cells[1][2] == CellState.FLOOR
    assert controller.grid.cells[1][1] == CellState.ENTRY
