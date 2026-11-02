import sys

from app import read_config
from app.backends.registry import get_backend
from app.engine import AppController


def main() -> None:
    """Executes the main routine of the maze generator."""

    print("Hello from a-maze-ing!")

    if len(sys.argv) != 2:
        print("Usage: a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config = read_config(sys.argv[1])

    if config:
        backend = get_backend(config.DISPLAY_MODE)
        controller = AppController(config, backend)
        controller.start()

    sys.exit(0)


if __name__ == "__main__":
    main()
