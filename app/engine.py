import random

from mazegen import create_stepping_generator, Maze, BaseGenerator
from app import Config
from app.grid import RenderGrid, CellState
from app.backends.base import GraphicBackend
from mazegen.utils import Direction


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
        self.is_generating = True
        self.show_path = False

        self.maze: Maze | None = None

        # self.maze = Maze(
        #     width=self.config.WIDTH,
        #     height=self.config.HEIGHT,
        #     m_entry=self.config.ENTRY,
        #     m_exit=self.config.EXIT,
        #     perfect=m_config.PERFECT
        # )

        self.grid = RenderGrid(
            width=self.width,
            height=self.height,
            m_entry=m_config.ENTRY,
            m_exit=m_config.EXIT
        )

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
        if not self.is_generating:
            return

        changed_cell = self.generator.step()
        if changed_cell is not None:
            x, y, dirs = changed_cell
            cx = (x * 2) + 1
            cy = (y * 2) + 1

            protected_cells = (CellState.ENTRY, CellState.EXIT, CellState.LOCK)
            if self.grid.cells[cy + dirs.dy][
                cx + dirs.dx] not in protected_cells:
                self.grid.cells[cy + dirs.dy][cx + dirs.dx] = CellState.FLOOR
        else:
            if self.maze is None:
                wn, we, ws, ww = self.generator.get_walls()
                self.maze = Maze(width=self.width,
                                 height=self.height,
                                 m_entry=self.config.ENTRY,
                                 m_exit=self.config.EXIT,
                                 perfect=self.config.PERFECT,
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

                    # nx = cx - 2 * dirs.dx
                    # ny = cy - 2 * dirs.dy
                    self.grid.cells[cy][cx] = CellState.PATH
                    self.grid.cells[wy][wx] = CellState.PATH
                    # self.grid.cells[ny][nx] = CellState.PATH
                else:
                    for y in range(self.grid.grid_height):
                        for x in range(self.grid.grid_width):
                            if self.grid.cells[y][x] == CellState.PATH:
                                self.grid.cells[y][x] = CellState.FLOOR
                    # self.grid.cells[self.maze.m_entry[0] * 2 + 1][self.maze.m_entry[1] * 2 + 1] = CellState.ENTRY
                    # self.grid.cells[self.maze.m_exit[0] * 2 + 1][self.maze.m_exit[1] * 2 + 1] = CellState.EXIT


                    # for y in range(self.height):
                    #     for x in range(self.width):
                for x, y in self.maze.path:
                    if (x, y) in self.maze.path:
                        self.grid.cells[y*2+1][x*2+1] = CellState.PATH
                        i = self.maze.path.index((x, y))
                        if i > 0:
                            nx, ny = self.maze.path[i - 1]
                            px = nx - x
                            py = ny - y
                            self.grid.cells[y * 2 + 1 + py][
                                x * 2 + 1 + px] = CellState.PATH

                self.grid.cells[self.maze.m_entry[1] * 2 + 1][self.maze.m_entry[0] * 2 + 1] = CellState.ENTRY
                self.grid.cells[self.maze.m_exit[1] * 2 + 1][self.maze.m_exit[0] * 2 + 1] = CellState.EXIT



    def handle_action(self, action: str) -> None:
        """Abstract central of action. Backends only send event strings here"""
        if action == "quit":
            self.is_running = False

        elif action == "regen":
            self.generator = self.create_generator()
            self.is_generating = True
            self.show_path = False
            self.grid.clear()

        # TODO: add path
        # TODO: save to file

        # entry_x, entry_y = self.config.ENTRY
        # exit_x, exit_y = self.config.EXIT
        # self.grid.cells[(entry_y * 2) + 1][
        #     (entry_x * 2) + 1] = CellState.ENTRY
        # self.grid.cells[(exit_y * 2) + 1][
        #     (exit_x * 2) + 1] = CellState.EXIT


    def start(self) -> None:
        self.backend.init_window(self.generator.width, self.generator.height,
                                 "A-Maze-ing <kbartosz> <kdzwigal>")
        self.backend.start_loop(controller=self)
