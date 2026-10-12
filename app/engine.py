import random
from enum import Enum, auto

from mazegen import create_stepping_generator, Maze, BaseGenerator
from app import Config
from app.grid import RenderGrid, CellState
from app.backends.base import GraphicBackend


class EngineState(Enum):
    INITIALIZING = auto()
    GENERATING = auto()
    IDLE = auto()
    SOLVING = auto()
    SOLVED = auto()
    PAUSED = auto()


class AppController:
    def __init__(self, m_config: Config, backend: GraphicBackend, ) -> None:
        self.config = m_config
        self.backend = backend

        self.width = m_config.WIDTH
        self.height = m_config.HEIGHT
        self.initial_seed: int | None = getattr(m_config, "SEED", None)
        self.algorithm_name = m_config.ALGORITHM

        self.current_seed: int = 0
        self.is_running = True
        # self.is_generating = True
        # self.show_path = False

        self.maze: Maze | None = None

        self.grid = RenderGrid(
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT
        )

        self.state: EngineState = EngineState.INITIALIZING

        self.generator = self.create_generator()

    def create_generator(self) -> BaseGenerator:
        """factory for generator and managing seed"""
        if self.initial_seed is not None:
            self.current_seed = self.initial_seed
        else:
            self.current_seed = random.randint(1, 999999)
            print(
                f"[ENGINE] initiating algorithm: "
                f"{self.algorithm_name}"
                f" with seed: {self.current_seed}"
            )

        return create_stepping_generator(
            algorithm_name=self.algorithm_name,
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT,
            perfect=self.config.PERFECT,
            seed=self.current_seed
        )

    # def change_algorithm_in_runtime(self, new_algorithm: str) -> None:
    #     if new_algorithm in get_available_algorithm():
    #         self.algorithm_name = new_algorithm
    #         print(
    #             f"[ENGINE] Changing algorithm class to "
    #             f"{new_algorithm} with seed: {self.current_seed}"
    #             f"it will be used after next regen"
    #         )

    def tick(self) -> None:
        """Performs exactly one logic step of application"""
        if self.grid.changed:
            return

        match self.state:
            case EngineState.GENERATING:
                self.generate_maze()
            case EngineState.IDLE:
                return
            case EngineState.SOLVING:
                self.solve()
            case EngineState.SOLVED:
                self.show_path()

    def handle_action(self, action: str) -> None:
        """Abstract central of action. Backends only send event strings here"""
        if action == "quit":
            self.is_running = False

        elif action == "regen":
            self.generator = self.create_generator()
            self.maze = None
            self.grid.clear()
            self.state = EngineState.GENERATING

        # TODO: add path
        # TODO: save to file

    def start(self) -> None:
        self.backend.init_window(self.generator.width,
                                 self.generator.height,
                                 "A-Maze-ing")
        self.state = EngineState.GENERATING
        self.backend.start_loop(controller=self)

    def generate_maze(self) -> None:

        changed_cell = self.generator.step()
        if changed_cell is not None:
            x, y, dirs = changed_cell
            cx = (x * 2) + 1
            cy = (y * 2) + 1

            self.grid.register_change(cx + dirs.dx, cy + dirs.dy,
                                      CellState.FLOOR)
        else:
            self.state = EngineState.SOLVING

    def solve(self) -> None:
        if self.maze is None:
            wn, we, ws, ww = self.generator.get_walls()
            self.maze = Maze(width=self.width,
                             height=self.height,
                             m_entry=self.config.ENTRY,
                             m_exit=self.config.EXIT,
                             perfect=self.config.PERFECT,
                             solver=self.config.SOLVER,
                             walls_n=wn,
                             walls_e=we,
                             walls_s=ws,
                             walls_w=ww)

        if self.maze is not None:
            path_cell = self.maze.step()
            if path_cell is not None:
                x, y, dirs = path_cell

                cx = (x * 2) + 1
                cy = (y * 2) + 1

                wx = cx - dirs.dx
                wy = cy - dirs.dy

                self.grid.register_change(cx, cy, CellState.PATH)
                self.grid.register_change(wx, wy, CellState.PATH)

            else:
                self.state = EngineState.SOLVED

    def show_path(self) -> None:
        if self.maze is None:
            return
        for y in range(self.grid.grid_height):
            for x in range(self.grid.grid_width):
                if self.grid.cells[y][x] == CellState.PATH:
                    self.grid.register_change(x, y,
                                              CellState.FLOOR)

        for x, y in self.maze.path:
            self.grid.register_change(x * 2 + 1, y * 2 + 1,
                                      CellState.PATH)

            i = self.maze.path.index((x, y))
            if i > 0:
                nx, ny = self.maze.path[i - 1]
                px = nx - x
                py = ny - y
                self.grid.register_change(x * 2 + 1 + px,
                                          y * 2 + 1 + py,
                                          CellState.PATH)
            gx_en = self.maze.m_entry[0] * 2 + 1
            gy_en = self.maze.m_entry[1] * 2 + 1
            if self.grid.cells[gy_en][gx_en] != CellState.ENTRY:
                self.grid.register_change(gx_en, gy_en,
                                          CellState.ENTRY)

            gx_ex = self.maze.m_exit[0] * 2 + 1
            gy_ex = self.maze.m_exit[1] * 2 + 1
            if self.grid.cells[gy_ex][gx_ex] != CellState.EXIT:
                self.grid.register_change(gx_ex, gy_ex,
                                          CellState.EXIT)
        self.state = EngineState.IDLE
