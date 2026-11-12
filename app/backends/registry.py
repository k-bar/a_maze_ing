"""Module responsible for loading and managing the application's
graphic backends."""
import sys
from typing import Callable

from app.backends.base import GraphicBackend


def _load_terminal() -> GraphicBackend:
    """
    Loads and initializes the terminal backend.

    Imports the TerminalBackend class at runtime (lazy loading) to avoid
    unnecessary memory overhead and circular dependencies.

    Returns:
        GraphicBackend: A ready-to-use instance of the terminal backend.
    """
    from app.backends.terminal import TerminalBackend
    return TerminalBackend()


def _load_mlx() -> GraphicBackend:
    """
    Loads and initializes the MLX backend.

    Imports the MlxBackend class at runtime (lazy loading).

    Returns:
        GraphicBackend: A ready-to-use instance of the MLX backend.
    """
    from app.backends.mlx import MlxBackend
    return MlxBackend()


BACKEND_REGISTRY: dict[str, Callable[[], GraphicBackend]] = {
    'TERMINAL': _load_terminal,
    'MLX': _load_mlx,
}
"""
Registry of available graphic backends.
Maps normalized mode names to initialization functions.
"""


def get_backend(display_mode: str) -> GraphicBackend:
    """
    Returns the appropriate backend instance based on the provided display mode.

    The function normalizes the input string (strips whitespace and converts
    to uppercase) and matches it against the backend registry. If no match
    is found, it prints a warning to standard error (stderr) and falls back
    to the default terminal backend.

    Args:
        display_mode (str): The name of the display mode (e.g., 'terminal', 'MLX').

    Returns:
        GraphicBackend: An initialized object of the selected graphic backend.
    """
    normalized_mode = display_mode.strip().upper()
    loader = BACKEND_REGISTRY.get(normalized_mode)
    if loader is None:
        print(
            f"[BACKEND] Warning: Unknown display mode: '{display_mode}'."
            f" Falling back to TERMINAL",
            file=sys.stderr)
        return _load_terminal()
    return loader()
