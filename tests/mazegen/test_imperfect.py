from typing import Generator

from mazegen import BaseGenerator, Maze
from mazegen.generators.imperfect import ImperfectGenerator
from mazegen.utils import Direction


class MockGenerator(BaseGenerator):
    def __init__(self) -> None:
        fake_maze = Maze(width=3, height=3, m_entry=(0, 0), m_exit=(2, 2),
                         perfect=False, seed=999)
        super().__init__(fake_maze)

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._animation_iterator)
        except StopIteration:
            return None

    def _algorithm_loop(self) \
            -> Generator[tuple[int, int, Direction], None, None]:
        # demolish walls between cell 0 and 3
        self.maze.walls_s &= ~(1 << 0)
        self.maze.walls_n &= ~(1 << 3)
        yield 0, 0, Direction.SOUTH
        # demolish walls between cell 3 and 6
        self.maze.walls_s &= ~(1 << 3)
        self.maze.walls_n &= ~(1 << 6)
        yield 0, 1, Direction.SOUTH

        self.maze.walls_e &= ~(1 << 6)
        self.maze.walls_w &= ~(1 << 7)
        yield 0, 2, Direction.EAST


def test_imperfect_generator_should_be_deterministic_and_remove_dead_ends() \
        -> None:
    base_gen_1 = MockGenerator()
    imperfect_gen_1 = ImperfectGenerator(base_gen_1)

    base_gen_2 = MockGenerator()
    imperfect_gen_2 = ImperfectGenerator(base_gen_2)

    steps_1 = []
    while (step := imperfect_gen_1.step()) is not None:
        steps_1.append(step)

    steps_2 = []
    while (step := imperfect_gen_2.step()) is not None:
        steps_2.append(step)

    assert steps_1 == steps_2
    assert len(steps_1) > 2
