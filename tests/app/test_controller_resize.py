import pytest

from app import Config
from app.backends.base import GraphicBackend
from app.engine import AppController, EngineState
from app.grid import RenderGrid


class MockBackend(GraphicBackend):
    def init_window(self, width: int, height: int, title: str) -> None: pass

    def start_loop(self, controller: AppController) -> None: pass

    def render_frame(self, grid: RenderGrid) -> None: pass


@pytest.fixture
def idle_controller() -> AppController:
    cfg = Config(WIDTH=10, HEIGHT=10, DISPLAY_MODE="MOCK")
    ctrl = AppController(cfg, MockBackend())
    ctrl.max_width = 100
    ctrl.max_height = 100
    ctrl.state = EngineState.IDLE
    return ctrl


def test_resize_grows_width_in_idle(idle_controller: AppController) -> None:
    idle_controller.handle_action("move_right")
    assert idle_controller.width == 11
    assert idle_controller.state == EngineState.IDLE
    idle_controller.handle_action("regen")
    assert getattr(idle_controller, "state") == EngineState.GENERATING


def test_resize_blocked_during_generation(
        idle_controller: AppController) -> None:
    idle_controller.state = EngineState.GENERATING
    idle_controller.handle_action("move_right")
    assert idle_controller.width == 11
    idle_controller.handle_action("regen")
    assert idle_controller.state == EngineState.GENERATING


def test_resize_during_pause_maintains_paused_state() -> None:
    cfg = Config(WIDTH=10, HEIGHT=10, DISPLAY_MODE="MOCK")
    ctrl = AppController(cfg, MockBackend())

    ctrl.state = EngineState.PAUSED
    ctrl.previous_state = EngineState.IDLE

    ctrl.handle_action("move_right")
    assert ctrl.width == 11
    assert ctrl.state == EngineState.PAUSED

    ctrl.handle_action("regen")
    assert ctrl.state == EngineState.PAUSED


def test_resize_at_maximum_limit_does_not_change_state_or_allocate(
        idle_controller: AppController) -> None:
    idle_controller.max_width = 15
    idle_controller.width = 15

    idle_controller.handle_action("move_right")

    assert idle_controller.width == 15
