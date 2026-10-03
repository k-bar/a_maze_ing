from app.engine import AppController
from app.backends.terminal import TerminalBackend
from app.grid import CellState
from mazegen.generator import MazeGenerator


def test_controller_tick_should_process_generator_step() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()

    backend.init_window(generator.width, generator.height, "Test Engine")
    controller = AppController(generator=generator, backend=backend)

    controller.tick()

    assert controller.grid.cells[1][1] == CellState.FLOOR


def test_controller_should_set_running_to_false_on_quit_action() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()
    backend.init_window(generator.width, generator.height, "Test Engine")
    controller = AppController(generator=generator, backend=backend)

    assert controller.is_running is True

    controller.handle_action("quit")
    assert controller.is_running is False


def test_controller_should_reset_generator_on_regen_action() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()
    backend.init_window(generator.width, generator.height, "Test Engine")
    controller = AppController(generator=generator, backend=backend)

    controller.tick()
    controller.tick()

    controller.handle_action("regen")

    assert controller.is_generating is True

    assert controller.grid.cells[1][1] == CellState.WALL


def test_controller_should_reset_generator_on_quit_action() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()
    backend.init_window(generator.width, generator.height, "Test Engine")
    controller = AppController(generator=generator, backend=backend)

    assert controller.is_generating is True
    assert controller.is_running is True

    controller.tick()

    controller.handle_action("regen")

    assert controller.is_generating is True
    assert controller.grid.cells[1][1] == CellState.WALL

    controller.handle_action("quit")
    assert controller.is_running is False


def test_controller_and_backend_interaction_on_action() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()
    backend.init_window(generator.width, generator.height, "Test")
    controller = AppController(generator=generator, backend=backend)

    assert controller.is_generating is True

    controller.tick()
    controller.handle_action("regen")

    assert controller.is_generating is True
    assert controller.grid.cells[1][1] == CellState.WALL


def test_should_correctly_modify_shared_grid_states_based_on_bits() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()
    controller = AppController(generator=generator, backend=backend)

    # simulate for cell  (1, 1) a mas
    # bit 0 (N) = 1 (closed)
    # bit 1 (E) = 0 (open)
    # bit 2 (S) = 1 (closed)
    # bit 3 (W) = 0 (open)
    # 0101 = 5 (decimal)

    cell_index = 4

    # enable bits for closed walls
    generator.walls_n = 1 << cell_index
    generator.walls_s = 1 << cell_index
    # disable bits for open walls
    generator.walls_e = ~(1 << cell_index)
    generator.walls_w = ~(1 << cell_index)

    # overwrite generator's iterator
    def single_step_mock() -> generator[tuple[int, int], None, None]:
        yield 1, 1

    generator.animation_iterator = single_step_mock()

    controller.tick()

    bx, by = 3, 3
    # center is always floor
    assert controller.grid.cells[by][bx] == CellState.FLOOR  # Open Center
    # closed cells (wall)
    assert controller.grid.cells[by - 1][bx] == CellState.WALL  # Open N wall
    assert controller.grid.cells[by + 1][bx] == CellState.WALL  # Open S wall
    # open cells (floor)
    assert controller.grid.cells[by][bx + 1] == CellState.FLOOR  # Open E wall
    assert controller.grid.cells[by][bx - 1] == CellState.FLOOR  # Open W wall
