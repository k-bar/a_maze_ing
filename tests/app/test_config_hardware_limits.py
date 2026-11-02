from typing import Any

import pytest
from _pytest.monkeypatch import MonkeyPatch
from pydantic import ValidationError

from app import Config, config_parser


@pytest.fixture
def mock_terminal_small(monkeypatch: MonkeyPatch) -> None:
    monkeypatch.setattr(config_parser, "_get_terminal_bounds",
                        lambda: (80, 24))


@pytest.fixture
def mock_terminal_error(monkeypatch: MonkeyPatch) -> None:
    import os

    def raise_os_error(*args: Any, **kwargs: Any) -> None:
        raise OSError("Inappropriate ioctl for device")

    monkeypatch.setattr(os, "get_terminal_size", raise_os_error)


def test_pydantic_rejects_huge_maze_for_terminal() -> None:
    bad_data = {"WIDTH": 60, "HEIGHT": 40, "DISPLAY_MODE": "TERMINAL"}

    try:
        Config.model_validate(bad_data)
        pytest.fail(
            "ERROR: Pydantic should throw ValidationError, "
            "and it passed data!")
    except ValidationError as e:
        assert "is too big for your console window" in str(e)


def test_pydantic_accepts_valid_maze_for_terminal(
        monkeypatch: MonkeyPatch) -> None:
    good_data = {"WIDTH": 10, "HEIGHT": 5, "DISPLAY_MODE": "TERMINAL"}

    config = Config.model_validate(good_data)
    assert config.WIDTH == 10
    assert config.HEIGHT == 5


def test_pydantic_accepts_exact_maximum_size_for_terminal(
        mock_terminal_small: None) -> None:
    """TERMINAL: Edge case - size exactly on limit
    for 80x24 max_w = (80-1)//2 = 39. max_h = (24-1-2)//2 = 10"""
    exact_data = {"WIDTH": 19, "HEIGHT": 8, "DISPLAY_MODE": "TERMINAL"}
    config = Config.model_validate(exact_data)
    assert config.WIDTH == 19
    assert config.HEIGHT == 8


def test_pydantic_uses_fallback_when_terminal_detection_fails(
        mock_terminal_error: None) -> None:
    bad_data = {"WIDTH": 60, "HEIGHT": 40, "DISPLAY_MODE": "TERMINAL"}
    try:
        Config.model_validate(bad_data)
        pytest.fail(
            "ERROR: Pydantic should use fallback 80x24 and reject data!")
    except ValidationError as e:
        assert "is too big for your console window" in str(e)


def test_pydantic_rejects_huge_maze_for_mlx() -> None:
    bad_mlx_data = {"WIDTH": 500, "HEIGHT": 500, "DISPLAY_MODE": "MLX"}
    try:
        Config.model_validate(bad_mlx_data)
        pytest.fail("ERROR: Pydantic should throw ValidationError for MLX!")
    except ValidationError as e:
        assert "is exceeding render limits for window" in str(e)
