from collections import deque
from ..maze_model import Maze, Wall


def solver_bfs(maze: 'Maze') -> list[tuple[int, int]]:
    """Find corridor from ENTRY to EXIT as BFS.
    """
    queue: deque[tuple[int, int]] = deque([maze.m_entry])

    visited: set[tuple[int, int]] = {maze.m_entry}

    came_from: dict[tuple[int, int], tuple[int, int] | None] \
        = {maze.m_entry: None}

    moves = {
        (0, -1): Wall.N,
        (1, 0): Wall.E,
        (0, 1): Wall.S,
        (-1, 0): Wall.W
    }

    while queue:
        current: tuple[int, int] | None = queue.popleft()

        if current == maze.m_exit:
            break

        if current is not None:
            x, y = current

        for (dx, dy), wall_flag in moves.items():
            nx, ny = x + dx, y + dy

            if (0 <= nx < maze.width and 0 <= ny < maze.height
                    and (nx, ny) not in maze.locked_cells):

                if (maze.grid[y][x] & wall_flag) == 0:

                    if (nx, ny) not in visited:
                        visited.add((nx, ny))
                        came_from[(nx, ny)] = current
                        queue.append((nx, ny))
                        yield (x, y, nx, ny)

    path = []
    curr: tuple[int, int] | None = maze.m_exit

    if curr not in came_from:
        print("?")
        return []

    while curr is not None:
        path.append(curr)
        curr = came_from[curr]

    path.reverse()
    maze.path = path
    return path
