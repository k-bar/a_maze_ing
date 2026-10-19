import random
from enum import Enum, auto

import numpy as np

from app.export_func import export_to_file
from mazegen import create_stepping_generator, Maze
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
        self.previous_state = EngineState.IDLE
        self.path_visible = True

        # self.maze: Maze | None = None

        self.grid = RenderGrid(
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT
        )

        self.state: EngineState = EngineState.INITIALIZING

        self.maze = self.create_generator()

    def create_generator(self) -> Maze:
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
            solver=self.config.SOLVER,
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
                # pass
                self.solve()
            case EngineState.SOLVED:
                # pass
                self.show_path()
            case EngineState.PAUSED:
                pass

    def handle_action(self, action: str) -> None:
        """Abstract central of action. Backends only send event strings here"""
        if action == "quit":
            self.is_running = False

        elif action == "regen":
            self.maze = self.create_generator()
            self.grid.clear()
            self.state = EngineState.GENERATING
        elif action == "hide_toggle":
            if self.state != EngineState.IDLE:
                return
            if self.path_visible:
                self.hide_path()
                self.path_visible = False
            else:
                self.show_path()
                self.path_visible = True
        elif action == "pause":
            if self.state == EngineState.PAUSED:
                self.state = self.previous_state
            else:
                self.previous_state = self.state
                self.state = EngineState.PAUSED

        elif action == "skip":
            if self.state == EngineState.GENERATING:
                self.generate_maze(skip=True)
                return
            if self.state == EngineState.SOLVING:
                self.solve(skip=True)

    def start(self) -> None:
        self.backend.init_window(self.width,
                                 self.height,
                                 "A-Maze-ing")
        self.state = EngineState.GENERATING
        self.backend.start_loop(controller=self)

    def generate_maze(self, skip: bool = False) -> None:

        while True:
            changed_cell = self.maze.step()
            if changed_cell is None:
                self.state = EngineState.SOLVING
                break
            x, y, dirs = changed_cell
            cx = (x * 2) + 1
            cy = (y * 2) + 1

            tx, ty = cx + dirs.dx, cy + dirs.dy
            if self.grid.cells[ty, tx] == CellState.FLOOR:
                new_state = CellState.WALL
            else:
                new_state = CellState.FLOOR
            self.grid.register_change(tx, ty, new_state)

            if not skip:
                break

    def solve(self, skip: bool = False) -> None:

        if self.maze is not None:
            while True:
                path_cell = self.maze.path_step()
                if path_cell is None:
                    self.state = EngineState.SOLVED
                    export_to_file(self.maze)
                    break
                x, y, dirs = path_cell

                cx = (x * 2) + 1
                cy = (y * 2) + 1

                wx = cx - dirs.dx
                wy = cy - dirs.dy

                self.grid.register_change(cx, cy, CellState.PATH)
                self.grid.register_change(wx, wy, CellState.PATH)

                if not skip:
                    break

    def show_path(self) -> None:
        if self.maze is None:
            return
        self.hide_path()

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
            if self.grid.cells[gy_en, gx_en] != CellState.ENTRY:
                self.grid.register_change(gx_en, gy_en,
                                          CellState.ENTRY)

            gx_ex = self.maze.m_exit[0] * 2 + 1
            gy_ex = self.maze.m_exit[1] * 2 + 1
            if self.grid.cells[gy_ex, gx_ex] != CellState.EXIT:
                self.grid.register_change(gx_ex, gy_ex,
                                          CellState.EXIT)
        self.state = EngineState.IDLE

    def hide_path(self) -> None:
        path_coordinates = np.argwhere(self.grid.cells == CellState.PATH)
        for y, x in path_coordinates:
            self.grid.register_change(x, y, CellState.FLOOR)
