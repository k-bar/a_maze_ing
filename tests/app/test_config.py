import pytest
from io import StringIO
from app.config_parser import read_and_parse


def test_should_parse_valid_config() -> None:
    valid_data = (
        "WIDTH=20\n"
        "HEIGHT=15\n"
        "ENTRY=1,1\n"
        "EXIT=19,14\n"
        "OUTPUT_FILE=maze.txt\n"
        "PERFECT=True\n"
    )

    fake_file = StringIO(valid_data)

    config = read_and_parse(fake_file)

    assert config.WIDTH == 20
    assert config.HEIGHT == 15
    assert config.ENTRY == (1, 1)
    assert config.EXIT == (19, 14)
    assert config.OUTPUT_FILE == "maze.txt"
    assert config.PERFECT is True


def test_should_parse_invalid_config() -> None:
    invalid_data = (
        "WIDTH=abc\n"
        "HEIGHT=-5\n"
    )

    fake_file = StringIO(invalid_data)
    with pytest.raises(ValueError):
        read_and_parse(fake_file)
