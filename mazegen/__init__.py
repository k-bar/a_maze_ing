from typing import Type

from .generators import WilsonGenerator, RecursiveBacktracker
from .generators.kruskal import KruskalGenerator
from .maze_model import Maze, Wall

_ALGORITHMS: dict[str, Type[Maze]] = {
    "KRUSKAL": KruskalGenerator,
    "WILSON": WilsonGenerator,
    "BACKTRACKER": RecursiveBacktracker,
}


# def generate_maze(
#         width: int,
#         height: int,
#         m_entry: tuple[int, int],
#         m_exit: tuple[int, int],
#         solver: str,
#         perfect: bool = True,
#         seed: int | None = None,
#         algorithm: str = "kruskal",
# ) -> Maze:
#     """Public autonomous export API for .whl (without animation)"""
#     if algorithm not in _ALGORITHMS:
#         raise ValueError(f"Algorithm {algorithm} not available")
#
#     generator_class = _ALGORITHMS[algorithm]
#     gen = generator_class(
#         width=width,
#         height=height,
#         m_entry=m_entry,
#         m_exit=m_exit,
#         perfect=perfect,
#         solver=solver,
#         seed=seed
#     )
#     gen.generate_all()
#
#     # wn, we, ws, ww = gen.get_walls()
#     return Maze(
#         width=width,
#         height=height,
#         m_entry=m_entry,
#         m_exit=m_exit,
#         perfect=perfect,
#         solver=solver,
#     )


def get_available_algorithm() -> list[str]:
    """Public function returning lists of available algorithms"""
    return list(_ALGORITHMS.keys())


def create_stepping_generator(
        algorithm_name: str,
        width: int,
        height: int,
        m_entry: tuple[int, int],
        m_exit: tuple[int, int],
        perfect: bool,
        solver: str,
        seed: int | None = None
) -> Maze:
    """Public factory for stepping generators for application engine"""
    if algorithm_name not in _ALGORITHMS:
        raise ValueError(f"Algorithm {algorithm_name} not available")

    generator_class = _ALGORITHMS[algorithm_name]
    gen = generator_class(width, height, m_entry, m_exit, perfect, solver,
                          seed)
    if not perfect:
        from mazegen.generators.imperfect import ImperfectGenerator
        return ImperfectGenerator(base_generator=gen)
    return gen


__all__ = ['Maze', 'Wall',  # "BaseGenerator",
           # 'get_locked_pattern_coords',
           "create_stepping_generator",
           # "generate_maze",
           "get_available_algorithm"]
