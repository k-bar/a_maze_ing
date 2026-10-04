import random
from typing import Type

from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.utils import Direction
from mazegen.base import BaseGenerator


class AppController:
    def __init__(self,
                 width: int,
                 height: int,
                 backend: GraphicBackend,
                 generator_class: Type[BaseGenerator],
                 initial_seed: int | None = None,
                 ) -> None:
        self.width = width
        self.height = height
        self.backend = backend
        self.generator_class = generator_class
        self.initial_seed = initial_seed

        self.current_seed: int = 0
        self.is_running = True
        self.is_generating = True

        self.grid = RenderGrid(width=width, height=height)

        self.generator: BaseGenerator = self.create_generator()

    def create_generator(self) -> BaseGenerator:
        """factory for generator and managing seed"""
        if self.initial_seed is not None:
            self.current_seed = self.initial_seed
        else:
            self.current_seed = random.randint(1, 999999)
            print(
                f"[ENGINE] initiating algorithm: "
                f"{self.generator_class.__name__}"
                f" with seed: {self.current_seed}"
            )
        return self.generator_class(width=self.width,
                                    height=self.height,
                                    seed=self.current_seed)

    def change_algorithm_class(self,
                               new_generator_class: Type[BaseGenerator]
                               ) -> None:
        print(
            f"[ENGINE] Changing algorithm class to "
            f"{new_generator_class.__name__}"
            f"it will be used after next regen"
        )
        self.generator_class = new_generator_class

    def tick(self) -> None:
        """Performs exactly one logic step of application"""
        if not self.is_generating:
            return

        changed_cell = self.generator.step()
        if changed_cell is None:
            self.is_generating = False
            return

        x, y = changed_cell
        walls_n, walls_e, walls_s, walls_w = self.generator.get_walls()
        cell_index = (y * self.generator.width) + x

        # center of the cell...
        cx = (x * 2) + 1
        cy = (y * 2) + 1
        # ...is always corridor (empty)
        self.grid.cells[cy][cx] = CellState.FLOOR

        masks = {0: walls_n, 1: walls_e, 2: walls_s, 3: walls_w}

        for bit_index, direction in enumerate(Direction):
            _, dy, dx = direction.value
            current_mask = masks[bit_index]
            if (current_mask & (1 << cell_index)) == 0:
                self.grid.cells[cy + dy][cx + dx] = CellState.FLOOR

    def handle_action(self, action: str) -> None:
        """Abstract central of action. Backends only send event strings here"""
        if action == "quit":
            self.is_running = False
        elif action == "regen":
            self.generator = self.create_generator()
            self.is_generating = True
            self.grid.clear()

    def start(self) -> None:
        self.backend.init_window(self.generator.width, self.generator.height,
                                 "BBB")
        self.backend.start_loop(controller=self)
