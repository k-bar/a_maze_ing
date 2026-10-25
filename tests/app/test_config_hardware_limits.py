import os

import pytest
from pydantic import ValidationError

from app import Config


def test_pydantic_rejects_huge_maze_for_terminal():
    bad_data = {
        "WIDTH": 60,
        "HEIGHT": 40,
        "DISPLAY_MODE": "TERMINAL"
    }

    class TestConfig(Config):
        def _get_termina_bounds(self) -> tuple[int, int]:
            return 80, 24

    try:
        TestConfig.model_validate(bad_data)
        pytest.fail(
            "ERROR: Pydantic should throw ValidationError, and it passed data!")
    except ValidationError as e:
        assert "is too big for your console window" in str(e)


def test_pydantic_accepts_valid_maze_for_terminal(monkeypatch):
    class TestConfig(Config):
        def _get_termina_bounds(self) -> tuple[int, int]:
            return 80, 24

    good_data = {
        "WIDTH": 10,
        "HEIGHT": 5,
        "DISPLAY_MODE": "TERMINAL"
    }

    config = TestConfig.model_validate(good_data)
    assert config.WIDTH == 10
    assert config.HEIGHT == 5

def test_pydantic_rejects_huge_maze_for_mlx():
    bad_mlx_data = {
        "WIDTH": 500,
        "HEIGHT": 500,
        "DISPLAY_MODE": "MLX"
    }
    try:
        Config.model_validate(bad_mlx_data)
        pytest.fail("ERROR: Pydantic should throw ValidationError for MLX!")
    except ValidationError as e:
        assert "is exceeding render limits for window" in str(e)