import random
import sys
from enum import Enum, auto
from typing import TypedDict

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


class ArrowMode(Enum):
    SIZE = auto()
    ENTRY = auto()
    EXIT = auto()


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
        self.solver_name: str = m_config.SOLVER

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

        self.arrow_mode: ArrowMode = ArrowMode.SIZE

        self.maze: Maze | None = None
        self.generator_process: BaseGenerator | None = None
        self.solver_process: MazeSolver | None = None

        self.is_entering_seed = False
        self.seed_input_buffer = ""

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

    def change_solver_in_runtime(self) -> None:
        from mazegen import get_available_solvers, create_stepping_solver
        available_solvers = get_available_solvers()
        try:
            current_idx = available_solvers.index(self.solver_name)
            next_idx = (current_idx + 1) % len(available_solvers)
            self.solver_name = available_solvers[next_idx]
        except ValueError:
            self.solver_name = available_solvers[0]

        print(f"[ENGINE] Changing solver class to {self.solver_name}")

        if self.state in [EngineState.IDLE, EngineState.SOLVING,
                          EngineState.SOLVED]:
            self.hide_path()
            assert self.maze is not None

            self.solver_process = create_stepping_solver(self.solver_name,
                                                         self.maze)
            self.state = EngineState.SOLVING

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

        if self.is_entering_seed:
            if action == "enter_action":
                if self.seed_input_buffer:
                    try:
                        self.initial_seed = int(self.seed_input_buffer)
                        assert self.initial_seed is not None
                        self.current_seed = self.initial_seed
                    except ValueError:
                        pass
                self.is_entering_seed = False
                self.handle_action("regen")
                return
            elif action == "seed_backspace":
                self.seed_input_buffer = self.seed_input_buffer[:-1]
                return
            elif action.startswith("digit_"):
                digit = action.split("_")[-1]
                if len(self.seed_input_buffer) < 6:
                    self.seed_input_buffer += digit
                return
            elif action == "pause":
                self.is_entering_seed = False
                return
            else:
                return

        match action:
            case "quit":
                self.is_running = False

            case "regen":
                self.init_new_run()
                self.grid.clear()
                self.state = EngineState.GENERATING
            case "hide_toggle":
                if self.state != EngineState.IDLE:
                    return
                if self.path_visible:
                    self.hide_path()
                    self.path_visible = False
                else:
                    self.show_path()
                    self.path_visible = True
            case "pause":
                if self.state == EngineState.PAUSED:
                    self.state = self.previous_state
                else:
                    self.previous_state = self.state
                    self.state = EngineState.PAUSED

            case "activate_seed_input":
                self.is_entering_seed = True
                self.seed_input_buffer = ""

            case "randomize_seed":
                self.initial_seed = random.randint(1, 999999)
                self.init_new_run()
                self.grid.clear()
                self.state = EngineState.GENERATING

            case "skip":
                if self.state == EngineState.PAUSED:
                    self.state = self.previous_state
                if self.state == EngineState.GENERATING:
                    self.generate_maze(skip=True)
                    return
                if self.state == EngineState.SOLVING:
                    self.solve(skip=True)

            case "enter_action":
                if self.state in [EngineState.GENERATING, EngineState.SOLVING]:
                    self.previous_state = self.state
                    self.state = EngineState.PAUSED
                    self.tick()
                elif self.state == EngineState.PAUSED:
                    self.state = self.previous_state
                    self.tick()
                    self.previous_state = self.state
                    self.state = EngineState.PAUSED

            case "cycle_maze_generator":
                self.change_algorithm_in_runtime()
                self.handle_action("regen")

            case "cycle_solver":
                self.change_solver_in_runtime()

            case "toggle_perfect":
                self.config.PERFECT = not self.config.PERFECT
                if self.maze:
                    self.maze.perfect = self.config.PERFECT
                if not self.config.PERFECT and self.generator_process:
                    from mazegen.generators.imperfect import ImperfectGenerator
                    if not isinstance(self.generator_process,
                                      ImperfectGenerator):
                        self.generator_process = ImperfectGenerator(
                            base_generator=self.generator_process)
                print(f"[ENGINE] Maze perfect property flipped in runtime to:"
                      f" {self.config.PERFECT}")

            case "toggle_arrow_mode":
                match self.arrow_mode:
                    case ArrowMode.SIZE:
                        self.arrow_mode = ArrowMode.ENTRY
                    case ArrowMode.ENTRY:
                        self.arrow_mode = ArrowMode.EXIT
                    case ArrowMode.EXIT:
                        self.arrow_mode = ArrowMode.SIZE
                print(
                    f"[ENGINE] Arrow keys mode switched to: "
                    f"{self.arrow_mode.name}")

            case "move_right" | "move_left" | "move_down" \
                 | "move_up":
                match self.arrow_mode:
                    case ArrowMode.SIZE:
                        new_w = self.width
                        new_h = self.height

                        if action == "move_right":
                            new_w += 1
                        elif action == "move_left":
                            new_w -= 1
                        elif action == "move_down":
                            new_h += 1
                        elif action == "move_up":
                            new_h -= 1
                        self.validate_and_apply_dimensions(new_w, new_h)
                        self.maze_resize()
                        self.handle_action("regen")
                    case ArrowMode.ENTRY | ArrowMode.EXIT:
                        dx, dy = 0, 0
                        if action == "move_up":
                            dy = -1
                        elif action == "move_down":
                            dy = 1
                        elif action == "move_right":
                            dx = 1
                        elif action == "move_left":
                            dx = -1

                        if self.arrow_mode == ArrowMode.ENTRY:
                            self._move_live_point("ENTRY", dx, dy)
                        else:
                            self._move_live_point("EXIT", dx, dy)

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

    def _move_live_point(self, point_type: str, dx: int, dy: int) -> None:
        current_x, current_y = self.config.ENTRY \
            if point_type == "ENTRY" else self.config.EXIT
        target_x = current_x + dx
        target_y = current_y + dy

        if not (0 <= target_x < self.width and 0 <= target_y < self.height):
            return

        other_x, other_y = self.config.EXIT \
            if point_type == "EXIT" else self.config.ENTRY
        if (target_x, target_y) == (other_x, other_y):
            return

        assert self.maze is not None
        if (target_x, target_y) in self.maze.locked_cells:
            return

        if point_type == "ENTRY":
            self.grid.register_change(current_x * 2 + 1, current_y * 2 + 1,
                                      CellState.FLOOR)
            self.config.ENTRY = (target_x, target_y)
            self.grid.register_change(target_x * 2 + 1, target_y * 2 + 1,
                                      CellState.ENTRY)

        else:
            self.grid.register_change(current_x * 2 + 1, current_y * 2 + 1,
                                      CellState.FLOOR)
            self.config.EXIT = (target_x, target_y)
            self.grid.register_change(target_x * 2 + 1, target_y * 2 + 1,
                                      CellState.EXIT)

        if self.state in [EngineState.IDLE, EngineState.SOLVING,
                          EngineState.SOLVED]:
            self.hide_path()
            from mazegen import create_stepping_solver
            assert self.maze is not None

            self.maze.m_entry = self.config.ENTRY
            self.maze.m_exit = self.config.EXIT

            self.solver_process = create_stepping_solver(self.config.SOLVER,
                                                         self.maze)
            self.state = EngineState.SOLVING

    class HudBlock(TypedDict):
        label: str
        value: str
        width_spec: int
        is_highlighted: bool
        is_seed: bool

    def get_unified_hud_blocks(self) -> list[HudBlock]:

        perf_suffix = "P" if self.config.PERFECT else "I"
        seed_display = f"{self.seed_input_buffer}_" \
            if self.is_entering_seed else str(self.current_seed)
        mode_name = self.arrow_mode.name

        return [
            {
                "label": "SEED",
                "value": seed_display,
                "width_spec": 13,
                "is_highlighted": self.is_entering_seed,
                "is_seed": True
            },
            {
                "label": "[A]LG",
                "value": f"{self.algorithm_name}({perf_suffix})",
                "width_spec": 16,
                "is_highlighted": False,
                "is_seed": False
            },
            {
                "label": "[S]OLV",
                "value": self.solver_name,
                "width_spec": 11,
                "is_highlighted": False,
                "is_seed": False
            },
            {
                "label": "SIZE",
                "value": f"{self.width}x{self.height}",
                "width_spec": 12,
                "is_highlighted": (
                        mode_name == "SIZE" and not self.is_entering_seed),
                "is_seed": False
            },
            {
                "label": "EDIT",
                "value": f"[{mode_name}]",
                "width_spec": 15,
                "is_highlighted": (
                        mode_name in ("ENTRY", "EXIT")
                        and not self.is_entering_seed),
                "is_seed": False
            },
            {
                "label": "STATE",
                "value": self.state.name,
                "width_spec": 17,
                "is_highlighted": False,
                "is_seed": False
            }
        ]

    def get_hud_controls_text(self, is_narrow: bool = False) -> str:
        if is_narrow:
            return ("ENTER:Confirm | BACKSPACE:Delete | SPACE:Cancel"
                    if self.is_entering_seed
                    else "1:Regen | K:Seed | TAB:Mode | 4:Quit")

        if self.is_entering_seed:
            return ("SEED INPUT MODE: [0-9] Type Digits | [BACKSPACE] Delete |"
                    " [ENTER] Confirm & Regen | [SPACE] Cancel")

        base_start = "CONTROLS: [R]egen | [K]ey Seed | Ra[N]d seed"
        base_end = "[C]olors | [TAB] Mode | [Q]uit"

        match self.state:
            case EngineState.GENERATING:
                core = " [SPACE] Pause  | [ENTER] Step | [END] Skip |"
            case EngineState.SOLVING:
                core = " [SPACE] Pause  | [ENTER] Step | [END] Skip |"
            case EngineState.IDLE | EngineState.SOLVED:
                core = f" [H] {'Hide' if self.path_visible else 'Show'} Path |"
            case EngineState.PAUSED:
                core = " [SPACE] Resume | [ENTER] Step | [END] Skip |"
            case _:
                core = ""
        return f"{base_start} | {core} {base_end}"
