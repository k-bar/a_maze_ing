from app.backends.base import GraphicBackend
from app.grid import RenderGrid, CellState
from app.utils import Direction
from mazegen.generator import MazeGenerator


class AppController:
    def __init__(self, generator: MazeGenerator,
                 backend: GraphicBackend) -> None:
        self.generator = generator
        self.backend = backend
        self.is_running = True
        self.is_generating = True
        self.grid = RenderGrid(width=generator.width,
                               height=generator.height)

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

        # cell_mask = 0
        # if (walls_n & (1 << cell_index)) != 0:
        #     cell_mask |= (1 << 0)
        # if (walls_e & (1 << cell_index)) != 0:
        #     cell_mask |= (1 << 1)
        # if (walls_s & (1 << cell_index)) != 0:
        #     cell_mask |= (1 << 2)
        # if (walls_w & (1 << cell_index)) != 0:
        #     cell_mask |= (1 << 3)

        # print('TUTAj', x, y)
        # self.backend.update_cell_in_buffer(x, y, cell_mask, self.grid)

    def handle_action(self, action: str) -> None:
        """Abstract central of action. Backends only send event strings here"""
        if action == "quit":
            self.is_running = False
        elif action == "regen":
            self.generator = MazeGenerator(width=self.generator.width,
                                           height=self.generator.height)
            self.is_generating = True
            self.grid.clear()
            self.backend.init_window(self.generator.width,
                                     self.generator.height, "AAA")

    def start(self) -> None:
        self.backend.init_window(self.generator.width, self.generator.height,
                                 "BBB")
        self.backend.start_loop(controller=self)

    # def start_animation(self) -> None:
    #     """Main loop with step by step animation"""
    #     # \033[?1049h   - enables alternative screen (no scrolling history)
    #     # \033[?25l     - hides blinking cursor
    #     print("\033[?1049h\033[?25l", end="")
    #     self.backend.init_window(self.generator.width, self.generator.height,
    #                              "AAA")
    #     try:
    #         self.is_running = True
    #         while self.is_running:
    #             self.is_generating = self.tick()
    #             self.backend.render_frame()
    #             if not self.is_generating:
    #                 self.is_running = False
    #
    #             time.sleep(0.05)
    #         time.sleep(2)
    #
    #     finally:  # Execute Around Pattern
    #         print("\033[?1049l\033[?25h", end="")
