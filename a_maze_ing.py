from mazegen.maze_class import Maze
from app.config_parser import read_config
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
        # maze.display_42()
        # maze.display_unicode()
        # maze.display()

        path = maze.solver_dfs()
        maze.display_solved(path)
        maze.export_to_file()
        maze.del_death_ends()
        print()
        path2 = maze.solver_dfs()
        path3 = maze.solver_bfs()
        maze.display_solved(path2)
        print()
        #maze.display_solved(path3)
        maze.display_solved_labyrynth(path3)
        maze.export_to_file()


    sys.exit(0)


if __name__ == "__main__":
    main()
