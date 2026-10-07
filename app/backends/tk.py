import tkinter as tk

from app.backends.base import GraphicBackend
from app.engine import AppController
from app.grid import CellState, RenderGrid


class TkBackend(GraphicBackend):
    BLOCK_SIZE = 30
    WALL_SIZE = BLOCK_SIZE // 10
    FRAME_DELAY_MS = 40
    COLORS = {
        CellState.WALL: "#332211",
        CellState.FLOOR: "#111111",
        CellState.ENTRY: "#00ff00",
        CellState.EXIT: "#ff0000",
        CellState.PATH: "#00ffff",
        CellState.LOCK: "#332211",
    }

    def __init__(self) -> None:
        self.root: tk.Tk | None = None
        self.canvas: tk.Canvas | None = None

    def init_window(self, width: int, height: int, title: str) -> None:
        pixel_width = width * self.BLOCK_SIZE + (width + 1) * self.WALL_SIZE
        pixel_height = height * self.BLOCK_SIZE + (height + 1) * self.WALL_SIZE

        self.root = tk.Tk()
        self.root.title(title)
        self.root.resizable(False, False)
        self.canvas = tk.Canvas(
            self.root,
            width=pixel_width,
            height=pixel_height,
            background=self.COLORS[CellState.FLOOR],
            highlightthickness=0,
        )
        self.canvas.pack()

    @classmethod
    def _axis_geometry(cls, index: int) -> tuple[int, int]:
        block_index = index // 2
        if index % 2 == 0:
            start = block_index * (cls.BLOCK_SIZE + cls.WALL_SIZE)
            return start, cls.WALL_SIZE

        start = (
            block_index * cls.BLOCK_SIZE
            + (block_index + 1) * cls.WALL_SIZE
        )
        return start, cls.BLOCK_SIZE

    def render_frame(self, grid: RenderGrid) -> None:
        if self.canvas is None:
            return

        self.canvas.delete("all")
        for y, row in enumerate(grid.cells):
            for x, state in enumerate(row):
                left, width = self._axis_geometry(x)
                top, height = self._axis_geometry(y)
                color = self.COLORS[state]
                self.canvas.create_rectangle(
                    left,
                    top,
                    left + width - 1,
                    top + height - 1,
                    fill=color,
                    outline=color,
                )

    def start_loop(self, controller: AppController) -> None:
        if self.root is None or self.canvas is None:
            raise RuntimeError("init_window must be called before start_loop")

        root = self.root

        def close_window() -> None:
            controller.handle_action("quit")
            root.quit()

        def handle_key(event: tk.Event) -> None:
            if event.keysym in ("1", "KP_1"):
                controller.handle_action("regen")
            elif event.keysym in ("4", "KP_4", "Escape"):
                close_window()

        def tick() -> None:
            if not controller.is_running:
                root.quit()
                return

            controller.tick()
            self.render_frame(controller.grid)
            root.after(self.FRAME_DELAY_MS, tick)

        root.protocol("WM_DELETE_WINDOW", close_window)
        root.bind("<KeyPress>", handle_key)
        self.render_frame(controller.grid)
        root.after(0, tick)
        root.mainloop()
