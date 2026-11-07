import pytest

from app import Config
from app.backends.base import GraphicBackend
from app.engine import AppController, EngineState, ArrowMode
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
    idle_controller.arrow_mode = ArrowMode.SIZE
    idle_controller.handle_action("move_right")
    assert idle_controller.width == 11
