from app import Config
from mazegen.generators import KruskalGenerator
import pytest


@pytest.fixture
def default_config() -> Config:
    return Config(
        WIDTH=15,
        HEIGHT=25,
        ENTRY=(0, 0),
        EXIT=(2, 2),
        PERFECT=True,
        ALGORITHM="KRUSKAL",
        SOLVER="BFS",
        SEED=123
    )


def test_maze_should_have_full_connectivity(default_config: Config) -> None:
    generator = KruskalGenerator(width=default_config.WIDTH,
                                 height=default_config.HEIGHT,
                                 m_entry=default_config.ENTRY,
                                 m_exit=default_config.EXIT,
                                 perfect=default_config.PERFECT,
                                 solver=default_config.SOLVER,
                                 seed=default_config.SEED)
    generator.generate_all()
    walls_n, walls_e, walls_s, walls_w = generator.get_walls()
    visited = set()

    queue = [(0, 0)]

    while queue:
        cx, cy = queue.pop(0)
        if (cx, cy) in visited:
            continue
        visited.add((cx, cy))

        cell_index = (cy * default_config.WIDTH) + cx
        if cy > 0 and (walls_n & (1 << cell_index)) == 0:
            queue.append((cx, cy - 1))
        if cx < default_config.WIDTH - 1 and (
                walls_e & (1 << cell_index)) == 0:
            queue.append((cx + 1, cy))
        if cy < default_config.HEIGHT - 1 and (
                walls_s & (1 << cell_index)) == 0:
            queue.append((cx, cy + 1))
        if cx > 0 and (walls_w & (1 << cell_index)) == 0:
            queue.append((cx - 1, cy))

    assert len(visited) == default_config.WIDTH * default_config.HEIGHT - 18


def test_perfect_maze_should_have_no_loops_or_cycles(
        default_config: Config) -> None:
    generator = KruskalGenerator(width=default_config.WIDTH,
                                 height=default_config.HEIGHT,
                                 m_entry=default_config.ENTRY,
                                 m_exit=default_config.EXIT,
                                 perfect=default_config.PERFECT,
                                 solver=default_config.SOLVER,
                                 seed=default_config.SEED)

    generator.generate_all()
    walls_n, walls_e, walls_s, walls_w = generator.get_walls()
    visited = set()

    has_cycle = False

    def dfs(cx: int, cy: int, px: int, py: int) -> bool:
        if (cx, cy) in visited:
            return True

        visited.add((cx, cy))

        cell_index = (cy * default_config.WIDTH) + cx

        # North
        if (
                cy >= 0
                and (walls_n & (1 << cell_index)) == 0
                and (cx, cy - 1) != (px, py)
        ):
            if dfs(cx, cy - 1, cx, cy):
                return True
        # East
        if (
                cx <= default_config.WIDTH - 1
                and (walls_e & (1 << cell_index)) == 0
                and (cx + 1, cy) != (px, py)
        ):
            if dfs(cx + 1, cy, cx, cy):
                return True

        # South
        if (
                cy <= default_config.HEIGHT - 1
                and (walls_s & (1 << cell_index)) == 0
                and (cx, cy + 1) != (px, py)
        ):
            if dfs(cx, cy + 1, cx, cy):
                return True

        # West
        if (
                cx >= 0
                and (walls_w & (1 << cell_index)) == 0
                and (cx - 1, cy) != (px, py)
        ):
            if dfs(cx - 1, cy, cx, cy):
                return True
        return False

    if dfs(0, 0, -1, -1):
        has_cycle = True

    assert has_cycle is False
    assert len(visited) == default_config.WIDTH * default_config.HEIGHT - 18
