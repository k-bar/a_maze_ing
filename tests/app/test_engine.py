from app.engine import AppController
from app.backends.terminal import TerminalBackend
from mazegen.generator import MazeGenerator


def test_controller_tick_should_process_generator_step() -> None:
    generator = MazeGenerator(width=3, height=3)
    backend = TerminalBackend()

    backend.init_window(generator.width, generator.height, "Test Engine")
    controller = AppController(generator=generator, backend=backend)

    controller.tick()

    assert backend.buffer[1][1] == " "


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

    assert backend.buffer[1][1] == "#"


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
    assert backend.buffer[1][1] == "#"

    controller.handle_action("quit")
    assert controller.is_running is False
