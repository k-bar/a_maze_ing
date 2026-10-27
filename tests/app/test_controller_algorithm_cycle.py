from app import Config
from app.backends.base import GraphicBackend
from app.engine import AppController, EngineState
from app.grid import RenderGrid
from mazegen import get_available_algorithm


class MockBackend(GraphicBackend):
    def init_window(self, width: int, height: int, title: str) -> None: pass

    def start_loop(self, controller: AppController) -> None: pass

    def render_frame(self, grid: RenderGrid) -> None: pass


def test_controller_cycles_algorithm_correctly() -> None:
    cfg = Config(WIDTH=10, HEIGHT=10, ALGORITHM="KRUSKAL", DISPLAY_MODE="MOCK")
    ctrl = AppController(cfg, MockBackend())
    ctrl.state = EngineState.IDLE

    available = get_available_algorithm()
    assert len(available) > 0

    current_idx = available.index("KRUSKAL")
    expected_algo = available[(current_idx + 1) % len(available)]

    ctrl.handle_action("cycle_maze_generator")

    assert ctrl.algorithm_name == expected_algo
    assert ctrl.state == EngineState.GENERATING
