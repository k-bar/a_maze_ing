from app.backends.base import GraphicBackend
from app.backends.terminal import TerminalBackend
from app.config_parser import read_config
import sys
import time
from app.engine import AppController


def main() -> None:
    """Executes the main routine of the maze generator.

    Validates the command-line arguments, expecting exactly one
    argument (the path to the configuration file). It then reads
    and parses the configuration, initializes the Maze object,
    and triggers its display methods in the terminal.

    Exits:
        0 on successful execution.
        1 if the incorrect number of arguments is provided.
    """
    print("Hello from a-maze-ing!")

    if len(sys.argv) != 2:
        print("Usage: a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config = read_config(sys.argv[1])

    if config:
        print(config)
        print(config.model_dump_json(indent=2))

        backend: GraphicBackend
        if config.DISPLAY_MODE == "Terminal":
            backend = TerminalBackend()
        elif sys.platform == "darwin":
            from app.backends.tk import TkBackend

            backend = TkBackend()
        else:
            from app.backends.mlx import MlxBackend

            backend = MlxBackend()
        controller = AppController(config, backend)

        print("\033[2J")
        print("START KURLA")
        time.sleep(1)
        controller.start()
        print("END KURLA")

    sys.exit(0)


if __name__ == "__main__":
    main()
