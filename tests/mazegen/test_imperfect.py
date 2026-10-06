from mazegen import BaseGenerator
from mazegen.generators.imperfect import ImperfectGenerator
from mazegen.utils import Direction


class MockBaseGenerator(BaseGenerator):
    def __init__(self):
        super().__init__(2, 2, (0, 0), (0, 0), True, 42)
        total_cells = 4
        full_mask = (1 << total_cells) - 1

        self.walls_n = full_mask
        self.walls_e = full_mask
        self.walls_s = full_mask
        self.walls_w = full_mask
        self.steps_counts = 0

    def step(self) -> tuple[int, int, Direction] | None:
        return None

    def get_walls(self) -> tuple[int, int, int, int]:
        return self.walls_n, self.walls_e, self.walls_s, self.walls_w

def test_imperfect_generator_should_be_deterministic_and_remove_dead_ends() -> None:
    base_gen_1 = MockBaseGenerator()
    base_gen_2 = MockBaseGenerator()

    imperfect_gen_1 = ImperfectGenerator(base_gen_1)
    imperfect_gen_2 = ImperfectGenerator(base_gen_2)

    steps_1 = []
    while (step:= imperfect_gen_1.step()) is not None:
        steps_1.append(step)

    steps_2 = []
    while (step:= imperfect_gen_2.step()) is not None:
        steps_2.append(step)


    assert steps_1 == steps_2
    assert len(steps_1) > 0


    wn, we, ws, ww = imperfect_gen_1.get_walls()

    walls_count = 0
    if (wn & (1 << 0)) !=0: walls_count += 1
    if (we & (1 << 1)) !=0: walls_count += 1
    if (ws & (1 << 2)) !=0: walls_count += 1
    if (ww & (1 << 3)) !=0: walls_count += 1

    assert walls_count < 3


