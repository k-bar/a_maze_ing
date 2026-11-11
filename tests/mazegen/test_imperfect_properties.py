import pytest

from mazegen import get_available_algorithms
from mazegen.maze_model import Maze
from mazegen import create_stepping_generator


def _generate_via_steps(algorithm: str, width: int, height: int,
                        seed: int) -> Maze:
    gen = create_stepping_generator(
        algorithm_name=algorithm,
        width=width,
        height=height,
        m_entry=(0, 0),
        m_exit=(width - 1, height - 1),
        perfect=False,
        seed=seed,
    )
    while gen.step() is not None:
        pass
    return gen.maze


def _has_open_3x3_room(maze: Maze) -> bool:
    """Returns True if there is any 3x3 area with zero internal walls."""
    if maze.width < 3 or maze.height < 3:
        return False

    _, we, ws, _ = maze.get_walls()
    width = maze.width

    for y in range(maze.height - 2):
        for x in range(width - 2):
            # Sprawdzamy 6 wewnętrznych ścian pionowych (EAST dla kolumn x i x+1)
            v_walls_closed = False
            v_walls_closed = False
            for dy in range(3):
                for dx in range(2):
                    idx = (y + dy) * width + (x + dx)
                    if we & (1 << idx):
                        v_walls_closed = True
                        break
                if v_walls_closed:
                    break

            if v_walls_closed:
                continue

            # Sprawdzamy 6 wewnętrznych ścian poziomych (SOUTH dla wierszy y i y+1)
            h_walls_closed = False
            for dy in range(2):
                for dx in range(3):
                    idx = (y + dy) * width + (x + dx)
                    if ws & (1 << idx):
                        h_walls_closed = True
                        break
                if h_walls_closed:
                    break

            if not h_walls_closed:
                return True

    return False


def _find_removable_dead_ends(maze: Maze) -> list[tuple[int, int]]:
    """Finds unlocked cells with 3 walls that have at least one closed wall to an unlocked neighbor."""
    wn, we, ws, ww = maze.get_walls()
    width = maze.width
    height = maze.height
    locked = set(maze.locked_cells)
    dead_ends: list[tuple[int, int]] = []

    for y in range(height):
        for x in range(width):
            if (x, y) in locked:
                continue

            bit = 1 << (y * width + x)
            wall_count = (
                    bool(wn & bit)
                    + bool(we & bit)
                    + bool(ws & bit)
                    + bool(ww & bit)
            )
            if wall_count == 3:
                has_removable_wall = (
                        (bool(wn & bit) and y > 0 and (x, y - 1) not in locked)
                        or (bool(we & bit) and x < width - 1 and (x + 1,
                                                                  y) not in locked)
                        or (bool(ws & bit) and y < height - 1 and (x,
                                                                   y + 1) not in locked)
                        or (bool(ww & bit) and x > 0 and (x - 1,
                                                          y) not in locked)
                )
                if has_removable_wall:
                    dead_ends.append((x, y))

    return dead_ends


@pytest.mark.parametrize("algorithm", get_available_algorithms())
@pytest.mark.parametrize(
    "width,height",
    [
        (3, 3),
        (3, 4),
        (5, 5),
        (10, 10),
        (20, 15),
        (30, 30),
    ],
)
@pytest.mark.parametrize("seed", list(range(1, 31)))
def test_imperfect_maze_has_no_3x3_open_rooms(
        algorithm: str, width: int, height: int, seed: int
) -> None:
    maze = _generate_via_steps(
        algorithm=algorithm,
        width=width,
        height=height,
        seed=seed,
    )
    assert not _has_open_3x3_room(maze), (
        f"Found open 3x3 room in {algorithm} ({width}x{height}, seed={seed})"
    )


@pytest.mark.parametrize("algorithm", get_available_algorithms())
@pytest.mark.parametrize(
    "width,height",
    [
        (3, 3),
        (3, 4),
        (5, 5),
        (10, 10),
        (20, 15),
        (30, 30),
    ],
)
@pytest.mark.parametrize("seed", list(range(1, 31)))
def test_imperfect_maze_has_no_remaining_dead_ends(
        algorithm: str, width: int, height: int, seed: int
) -> None:
    maze = _generate_via_steps(
        algorithm=algorithm,
        width=width,
        height=height,
        seed=seed,
    )
    remaining = _find_removable_dead_ends(maze)
    assert not remaining, (
        f"Found {len(remaining)} remaining dead ends in {algorithm} "
        f"({width}x{height}, seed={seed}): {remaining[:5]}"
    )
# pytest tests/mazegen/test_imperfect_properties.py -k
# "no_remaining_dead_ends" --tb=short -q
