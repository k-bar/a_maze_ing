import subprocess
from typing import Any

from _pytest.monkeypatch import MonkeyPatch

from app.backends.mlx import get_screen_resolution


def test_get_screen_resolution_success(monkeypatch: MonkeyPatch) -> None:
    mock_output = ("Screen 0: minimum 320 x 200, current 1920 x 1080, "
                   "maximum 16384 x 16384")
    monkeypatch.setattr(subprocess, "check_output",
                        lambda *args, **kwargs: mock_output)
    w, h = get_screen_resolution(fallback=(1280, 720))
    assert w == 1920
    assert h == 1080


def test_get_screen_resolution_failure_returns_fallback(
        monkeypatch: MonkeyPatch) -> None:
    def mock_raise(*args: Any, **kwargs: Any) -> None:
        raise subprocess.CalledProcessError(1, "xrandr")

    monkeypatch.setattr(subprocess, "check_output", mock_raise)
    w, h = get_screen_resolution(fallback=(1024, 768))
    assert w == 1024
    assert h == 768
