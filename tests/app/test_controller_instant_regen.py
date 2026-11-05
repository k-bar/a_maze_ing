import typing

from app import Config
from app.backends.base import GraphicBackend
from app.engine import AppController, EngineState
from app.grid import RenderGrid


class MockBackend(GraphicBackend):
    def init_window(self, width: int, height: int, title: str) -> None: pass

    def start_loop(self, controller: AppController) -> None: pass

    def render_frame(self, grid: RenderGrid) -> None: pass

    def update_geometry(self, width: int, height: int) -> None: pass


def test_resize_forces_instant_generating_state() -> None:
    cfg = Config(WIDTH=10, HEIGHT=10, DISPLAY_MODE="MOCK")
    ctrl = AppController(cfg, MockBackend())

    state_var: EngineState = EngineState.IDLE
    ctrl.state = state_var

    ctrl.init_new_run()
    ctrl.handle_action("move_right")
    assert ctrl.width == 11
    assert ctrl.state == EngineState.IDLE
    ctrl.handle_action("regen")
    assert typing.cast(EngineState, ctrl.state) == EngineState.GENERATING
