"""
Public API for the mazegen package.

Provides high-level functions to generate and solve mazes autonomously,
as well as factory functions to create stepping generators and solvers
for step-by-step execution and animation.
"""
from typing import Type

from .generators import KruskalGenerator, WilsonGenerator, \
    RecursiveBacktracker, BaseGenerator, PrimGenerator, ImperfectGenerator
from .maze_model import Maze, Wall
from .solvers import MazeSolver
from .solvers.bfs import BFSSolver
from .solvers.dfs import DFSSolver
from .solvers.astar import AStarSolver
from .utils import Direction

_ALGORITHMS: dict[str, Type[BaseGenerator]] = {
    "KRUSKAL": KruskalGenerator,
    "WILSON": WilsonGenerator,
    "BACKTRACKER": RecursiveBacktracker,
    "PRIM": PrimGenerator,
}

_SOLVERS: dict[str, type[MazeSolver]] = {
    "BFS": BFSSolver,
    "DFS": DFSSolver,
    "ASTAR": AStarSolver,
}


def generate_maze(
        width: int,
        height: int,
        m_entry: tuple[int, int],
        m_exit: tuple[int, int],
        algorithm: str = "BACKTRACKER",
        perfect: bool = True,
        seed: int | None = None,

) -> Maze:
    """
    Generate a complete maze synchronously.

    This function serves as the autonomous export API, creating the maze
    object and executing the generation algorithm from start to finish
    without animation steps.

    Args:
        width (int): The width of the maze in cells.
        height (int): The height of the maze in cells.
        m_entry (tuple[int, int]): The (x, y) coordinates for the maze
        entrance.
        m_exit (tuple[int, int]): The (x, y) coordinates for the maze exit.
        algorithm (str, optional): The generation algorithm to use. Defaults
        to "BACKTRACKER".
        perfect (bool, optional): If True, generates a perfect maze (no loops,
        exactly one solution).
            If False, generates a braided/imperfect maze. Defaults to True.
        seed (int | None, optional): Random seed for reproducibility. Defaults
        to None.

    Returns:
        Maze: The fully generated maze object.

    Raises:
        ValueError: If the specified algorithm is not supported.
    """
    upper_algorithm = algorithm.upper()

    if upper_algorithm not in _ALGORITHMS:
        raise ValueError(f"Algorithm {algorithm} not available")

    maze = Maze(
        width=width,
        height=height,
        m_entry=m_entry,
        m_exit=m_exit,
        perfect=perfect,
        seed=seed
    )
    generator_class = _ALGORITHMS[upper_algorithm]
    gen = generator_class(maze)
    if not perfect:
        gen = ImperfectGenerator(base_generator=gen)
    gen.generate_all()

    return maze


def solve_maze(maze: Maze, algorithm: str = "BFS") -> list[tuple[int, int]]:
    """
    Solve a given maze synchronously using a specified algorithm.

    Args:
        maze (Maze): The generated maze instance to be solved.
        algorithm (str, optional): The solving algorithm to use ("BFS", "DFS",
        "ASTAR").
            Defaults to "BFS".

    Returns:
        list[tuple[int, int]]: A list of (x, y) coordinates representing
        the path from the maze entry to the exit.

    Raises:
        ValueError: If the specified solver algorithm is not supported.
    """
    upper_solver = algorithm.upper()
    if upper_solver not in _SOLVERS:
        raise ValueError(f"Solver {algorithm} not available")
    solver_class = _SOLVERS[upper_solver]
    solver_process = solver_class(maze)

    return solver_process.solve_all()


def get_available_algorithms() -> list[str]:
    """
    Retrieve a list of all supported maze generation algorithms.

    Returns:
        list[str]: The string keys of available algorithms
        (e.g., 'KRUSKAL', 'WILSON').
    """
    return list(_ALGORITHMS.keys())


def get_available_solvers() -> list[str]:
    """
    Retrieve a list of all supported maze solving algorithms.

    Returns:
        list[str]: The string keys of available solvers
        (e.g., 'BFS', 'DFS', 'ASTAR').
    """
    return list(_SOLVERS.keys())


def create_stepping_generator(
        algorithm_name: str,
        width: int,
        height: int,
        m_entry: tuple[int, int],
        m_exit: tuple[int, int],
        perfect: bool,
        seed: int | None = None
) -> BaseGenerator:
    """
    Create a maze generator instance for step-by-step execution.

    This factory function is intended for application engines that require
    visual
    animation of the generation process rather than an instantaneous result.

    Args:
        algorithm_name (str): The generation algorithm to initialize.
        width (int): The width of the maze in cells.
        height (int): The height of the maze in cells.
        m_entry (tuple[int, int]): The (x, y) coordinates for the maze
        entrance.
        m_exit (tuple[int, int]): The (x, y) coordinates for the maze exit.
        perfect (bool): If True, configures a perfect maze generator. If False,
            wraps the generator in an ImperfectGenerator to create loops.
        seed (int | None, optional): Random seed for reproducibility. Defaults
        to None.

    Returns:
        BaseGenerator: An initialized generator instance ready for step
        iteration.

    Raises:
        ValueError: If the requested algorithm is not supported.
    """
    upper_algorithm = algorithm_name.upper()
    if algorithm_name not in _ALGORITHMS:
        raise ValueError(f"Algorithm {algorithm_name} not available")

    maze = Maze(width, height, m_entry, m_exit, perfect, seed)

    generator_class = _ALGORITHMS[upper_algorithm]
    gen = generator_class(maze)
    if not perfect:
        from mazegen.generators.imperfect import ImperfectGenerator
        return ImperfectGenerator(base_generator=gen)
    return gen


def create_stepping_solver(solver_name: str, maze: Maze) -> MazeSolver:
    """
    Create a maze solver instance for step-by-step execution.

    This factory function is designed for application engines that animate the
    pathfinding process.

    Args:
        solver_name (str): The solving algorithm to initialize
        ("BFS", "DFS", "ASTAR").
        maze (Maze): The maze instance to be solved.

    Returns:
        MazeSolver: An initialized solver instance ready for step iteration.

    Raises:
        ValueError: If the requested solver algorithm is not supported.
    """
    upper_solver = solver_name.upper()
    if solver_name not in _SOLVERS:
        raise ValueError(f"Solver {solver_name} not available")
    return _SOLVERS[upper_solver](maze)


__all__ = ['Maze', 'Wall', "Direction",
           "BaseGenerator",
           "create_stepping_generator",
           "create_stepping_solver",
           "generate_maze",
           "solve_maze",
           "get_available_algorithms",
           "get_available_solvers"]
