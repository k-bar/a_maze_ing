import sys
from typing import Callable

from app.backends.base import GraphicBackend


def _load_terminal() -> GraphicBackend:
    from app.backends.terminal import TerminalBackend
    return TerminalBackend()


def _load_mlx() -> GraphicBackend:
    from app.backends.mlx import MlxBackend
    return MlxBackend()


BACKEND_REGISTRY: dict[str, Callable[[], GraphicBackend]] = {
    'TERMINAL': _load_terminal,
    'MLX': _load_mlx,
}


def get_backend(display_mode: str) -> GraphicBackend:
    normalized_mode = display_mode.strip().upper()
    loader = BACKEND_REGISTRY.get(normalized_mode)
    if loader is None:
        print(
            f"[BACKEND] Warning: Unknown display mode: '{display_mode}'."
            f" Falling back to TERMINAL",
            file=sys.stderr)
        raise RuntimeError(
            "Critical: TERMINAL backend loader not found in registry.")
    return loader()
