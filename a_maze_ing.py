import logging
import subprocess
import sys

from app import read_config
from app.backends.registry import get_backend
from app.engine import AppController

logging.basicConfig(
    filename="maze_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main() -> None:
    """Executes the main routine of the maze generator."""

    print("Hello from a-maze-ing!")

    if len(sys.argv) != 2:
        print("Usage: a_maze_ing.py config.txt", file=sys.stderr)
        sys.exit(1)

    config = read_config(sys.argv[1])
    if not config:
        raise ValueError("Configuration file is empty or invalid.")

    backend = get_backend(config.DISPLAY_MODE)
    controller = AppController(config, backend)
    controller.start()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
    except Exception as e:
        logging.critical("Unhandled application error", exc_info=True)
        print(f"\n[CRITICAL ERROR] {e}", file=sys.stderr)
        print("Technical details saved to maze_errors.log.", file=sys.stderr)
        sys.exit(1)
    finally:
        try:
            subprocess.run(
                ["xset", "r", "on"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass
