from typing import Type

from .generators import KruskalGenerator, WilsonGenerator, \
    RecursiveBacktracker, BaseGenerator, PrimGenerator, ImperfectGenerator
from .maze_model import Maze, Wall
from .solvers import MazeSolver
from .solvers.bfs import BFSSolver
from .solvers.dfs import DFSSolver
from .utils import Direction
_ALGORITHMS: dict[str, Type[BaseGenerator]] = {
    "KRUSKAL": KruskalGenerator,
    "WILSON": WilsonGenerator,
    "BACKTRACKER": RecursiveBacktracker,
    "PRIM": PrimGenerator,
}

_SOLVERS = {
    "BFS": BFSSolver,
    "DFS": DFSSolver
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
    """Public autonomous export API for .whl (without animation)"""
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
    upper_solver = algorithm.upper()
    if upper_solver not in _SOLVERS:
        raise ValueError(f"Solver {algorithm} not available")
    solver_class = _SOLVERS[upper_solver]
    solver_process = solver_class(maze)

    return solver_process.solve_all()


def get_available_algorithm() -> list[str]:
    """Public function returning lists of available algorithms"""
    return list(_ALGORITHMS.keys())


def get_available_solvers() -> list[str]:
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
    """Public factory for stepping generators for application engine"""
    if algorithm_name not in _ALGORITHMS:
        raise ValueError(f"Algorithm {algorithm_name} not available")

    maze = Maze(width, height, m_entry, m_exit, perfect, seed)

    generator_class = _ALGORITHMS[algorithm_name]
    gen = generator_class(maze)
    if not perfect:
        from mazegen.generators.imperfect import ImperfectGenerator
        return ImperfectGenerator(base_generator=gen)
    return gen


def create_stepping_solver(solver_name: str, maze: Maze) -> MazeSolver:
    if solver_name not in _SOLVERS:
        raise ValueError(f"Solver {solver_name} not available")
    return _SOLVERS[solver_name](maze)


__all__ = ['Maze', 'Wall', "Direction",
           "BaseGenerator",
           "create_stepping_generator",
           "create_stepping_solver",
           "generate_maze",
           "solve_maze",
           "get_available_algorithm",
           "get_available_solvers"]
