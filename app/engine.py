import random
import sys
from enum import Enum, auto

import numpy as np

from app.export_func import export_to_file
from mazegen import create_stepping_generator, Maze, BaseGenerator
from app import Config
from app.grid import RenderGrid, CellState
from app.backends.base import GraphicBackend
from mazegen.solvers import MazeSolver


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

        self.max_width: int = getattr(backend, "max_width", 300)
        self.max_height: int = getattr(backend, "max_height", 150)

        self.initial_seed: int | None = getattr(m_config, "SEED", None)
        self.algorithm_name: str = m_config.ALGORITHM

        self.current_seed: int = 0
        self.is_running = True
        self.previous_state = EngineState.IDLE
        self.path_visible = True

        self.grid = RenderGrid(
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT
        )

        self.state: EngineState = EngineState.INITIALIZING

        self.maze: Maze | None = None
        self.generator_process: BaseGenerator | None = None
        self.solver_process: MazeSolver | None = None

        self.init_new_run()

    def init_new_run(self) -> None:
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

        self.generator_process = create_stepping_generator(
            algorithm_name=self.algorithm_name,
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT,
            perfect=self.config.PERFECT,
            # solver=self.config.SOLVER,
            seed=self.current_seed
        )

        assert self.generator_process is not None
        self.maze = self.generator_process.maze
        assert self.maze is not None
        self.solver_process = None

    def change_algorithm_in_runtime(self) -> None:
        from mazegen import get_available_algorithm
        available_algos = get_available_algorithm()
        try:
            current_idx = available_algos.index(self.algorithm_name)
            next_idx = (current_idx + 1) % len(available_algos)
            self.algorithm_name = available_algos[next_idx]
        except ValueError:
            self.algorithm_name = available_algos[0]

        print(
            f"[ENGINE] Changing algorithm class to "
            f"{self.algorithm_name} with seed: {self.current_seed}"
            f"it will be used after next regen",
            file=sys.stderr
        )

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
            self.init_new_run()
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

        elif action == "cycle_maze_generator":
            self.change_algorithm_in_runtime()
            self.handle_action("regen")

        elif action in ["grow_width", "shrink_width", "grow_height",
                        "shrink_height"]:
            new_w = self.width
            new_h = self.height

            if action == "grow_width":
                new_w += 1
            elif action == "shrink_width":
                new_w -= 1
            elif action == "grow_height":
                new_h += 1
            elif action == "shrink_height":
                new_h -= 1
            self.validate_and_apply_dimensions(new_w, new_h)
            # self.config.EXIT = (self.width - 1)
            self.maze_resize()
            self.handle_action("regen")

    def start(self) -> None:
        self.backend.init_window(self.width,
                                 self.height,
                                 "A-Maze-ing")
        self.state = EngineState.GENERATING
        self.backend.start_loop(controller=self)

    def generate_maze(self, skip: bool = False) -> None:

        while True:
            assert self.generator_process is not None
            changed_cell = self.generator_process.step()
            if changed_cell is None:
                assert self.maze is not None
                from mazegen import create_stepping_solver
                self.solver_process = create_stepping_solver(
                    self.config.SOLVER, self.maze)
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
                assert self.solver_process is not None
                path_cell = self.solver_process.step()
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

    def maze_resize(self) -> None:
        print(
            f"[ENGINE] Resize action executed. New logical size: "
            f"{self.width}x{self.height}", file=sys.stderr)

        self.backend.update_geometry(self.width, self.height)

        from app.grid import RenderGrid
        self.grid = RenderGrid(
            width=self.width,
            height=self.height,
            m_entry=self.config.ENTRY,
            m_exit=self.config.EXIT
        )

    def validate_and_apply_dimensions(self, target_width: int,
                                      target_height: int) -> None:

        current_ex, current_ey = self.config.EXIT
        validated_ex = min(current_ex, self.width - 1)
        validated_ey = min(current_ey, self.height - 1)
        self.config.EXIT = (validated_ex, validated_ey)

        min_size = 3
        max_w = getattr(self, "max_width", 100)
        max_h = getattr(self, "max_height", 100)
        self.width = max(min_size, min(target_width, max_w))
        self.height = max(min_size, min(target_height, max_h))

        en_x, en_y = self.config.ENTRY
        self.config.ENTRY = (min(en_x, self.width - 1),
                             min(en_y, self.height - 1))

        ex_x, ex_y = self.config.EXIT
        self.config.EXIT = (min(ex_x, self.width - 1),
                            min(ex_y, self.height - 1))

        if self.maze is not None:
            if (hasattr(self, "LOCKE_CELLS")
                    and isinstance(self.maze.locked_cells, list)):
                validate_locks = []
                for lx, ly in self.maze.locked_cells:
                    validate_locks.append((min(lx, self.width - 1),
                                           min(ly, self.height - 1)))
                self.maze.locked_cells = validate_locks

        print(
            f"[ENGINE] Validated dimensions applied:"
            f" {self.width}x{self.height}")
