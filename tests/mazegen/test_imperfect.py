from typing import Generator

from mazegen import BaseGenerator
from mazegen.generators.imperfect import ImperfectGenerator
from mazegen.utils import Direction


class MockBaseGenerator(BaseGenerator):
    def __init__(self) -> None:
        super().__init__(3, 3, (0, 0), (2, 2), True, 42)
        total_cells = 9
        full_mask = (1 << total_cells) - 1

        self.walls_n = full_mask
        self.walls_e = full_mask
        self.walls_s = full_mask
        self.walls_w = full_mask

        self._iterator = self._run_mock_steps()

    def step(self) -> tuple[int, int, Direction] | None:
        try:
            return next(self._iterator)
        except StopIteration:
            return None

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

    def _run_mock_steps(self) -> (
            Generator)[tuple[int, int, Direction], None, None]:

        # demolish walls between cell 0 and 3
        self.walls_s &= ~(1 << 0)
        self.walls_n &= ~(1 << 3)
        yield 0, 0, Direction.SOUTH
        # demolish walls between cell 3 and 6
        self.walls_s &= ~(1 << 3)
        self.walls_n &= ~(1 << 6)
        yield 0, 1, Direction.SOUTH


def test_imperfect_generator_should_be_deterministic_and_remove_dead_ends() \
        -> None:
    base_gen_1 = MockBaseGenerator()
    imperfect_gen_1 = ImperfectGenerator(base_gen_1)
    imperfect_gen_1.seed = 999

    base_gen_2 = MockBaseGenerator()
    imperfect_gen_2 = ImperfectGenerator(base_gen_2)
    imperfect_gen_2.seed = 999

    print("cos", imperfect_gen_1.get_walls())
    steps_1 = []
    while (step := imperfect_gen_1.step()) is not None:
        steps_1.append(step)

    steps_2 = []
    while (step := imperfect_gen_2.step()) is not None:
        steps_2.append(step)

    assert steps_1 == steps_2
    assert len(steps_1) > 2
