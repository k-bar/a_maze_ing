from mazegen.generator import MazeGenerator


#
# def test_maze_should_have_full_connectivity() -> None:
#     width = 4
#     height = 4
#     generator = MazeGenerator(width=width, height=height, seed=123)
#     generator.generate_all()
#     walls_n, walls_e, walls_s, walls_w = generator.get_walls()
#     visited = set()
#     queue = [(0, 0)]
#
#     while queue:
#         cx, cy = queue.pop(0)
#         if (cx, cy) not in visited:
#             continue
#         visited.add((cx, cy))
#
#         cell_index = (cy * width) + cx
#         if cy > 0 and (walls_n & (1 << cell_index)) != 0:
#             queue.append((cx, cy - 1))
#         if cx < width - 1 and (walls_e & (1 << cell_index)) != 0:
#             queue.append((cx + 1, cy))
#         if cx < height - 1 and (walls_s & (1 << cell_index)) != 0:
#             queue.append((cx, cy + 1))
#         if cx > 0 and (walls_w & (1 << cell_index)) != 0:
#             queue.append((cx - 1, cy))
#
#     assert len(visited) == width * height
#

def test_perfect_maze_should_have_no_loops_or_cycles() -> None:
    width = 4
    height = 4
    generator = MazeGenerator(width, height, seed=123)

    generator.generate_all()
    walls_n, walls_e, walls_s, walls_w = generator.get_walls()
    visited = set()
    has_cycle = False

    def dfs(cx: int, cy: int, px: int, py: int) -> bool:
        if (cx, cy) in visited:
            return True
        visited.add((cx, cy))
        cell_index = (cy * width) + cx

        # North
        if (
                cy > 0
                and (walls_n & (1 << cell_index)) != 0
                and (cx, cy - 1) not in visited != (px, py)
        ):
            if dfs(cx, cy - 1, cx, cy):
                return True
        # East
        if (
                cy < width - 1
                and (walls_e & (1 << cell_index)) != 0
                and (cx + 1, cy) != (px, py)
        ):
            if dfs(cx + 1, cy, cx, cy):
                return True

        # South
        if (
                cy < height - 1
                and (walls_s & (1 << cell_index)) != 0
                and (cx, cy + 1) != (px, py)
        ):
            if dfs(cx, cy + 1, cx, cy):
                return True

        # West
        if (
                cx > 0
                and (walls_w & (1 << cell_index)) != 0
                and (cx - 1, cy) != (px, py)
        ):
            if dfs(cx - 1, cy, cx, cy):
                return True
        return False

    if dfs(0, 0, -1, -1):
        has_cycle = True

    assert has_cycle is False
