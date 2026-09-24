from .maze_pars_42 import Maze, read_config
import sys


def main() -> None:
    print("Hello from a-maze-ing!")

    if len(sys.argv) != 2:
        print("Usage: a_maze_ing.py config.txt")
        sys.exit(1)
    config = read_config(sys.argv[1])
    if config:
        print(config)
        print(config.model_dump_json(indent=2))
        maze = Maze(config)
        maze.display_42()
        maze.display_unicode()
        # maze.display()
    sys.exit(0)


if __name__ == "__main__":
    main()
