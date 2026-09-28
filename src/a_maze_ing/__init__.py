"""
Main entry point for the a-maze-ing application.
Handles command-line arguments, configuration loading, 
and maze initialization and display.
"""

from .maze_pars_42 import Maze, read_config
import sys


def main() -> None:
    """
    Executes the main routine of the maze generator.

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