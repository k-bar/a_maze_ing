# import random
# from ..maze_model import Maze
# from ..maze_model import Wall
#
#
# def del_death_ends(maze: 'Maze') -> None:
#     """Remove walls from eligible dead-end cells.
#
#     Scans the maze in row-major order. For each unlocked cell with exactly
#     three walls, removes a randomly selected wall to an eligible neighboring
#     cell, if one exists. The maze grid is modified in place. Random choices
#     are initialized using the maze seed.
#
#     Args:
#         maze: Maze whose dead ends should be opened.
#     """
#     random.seed(maze.seed)
#     visited: set[tuple[int, int]] = set()
#     for y in range(maze.height):
#         for x in range(maze.width):
#             if (x, y) not in maze.locked_cells:
#
#                 cell = maze.grid[y][x]
#
#                 wall_count: int = (bool(cell & Wall.W)
#                                    + bool(cell & Wall.E)
#                                    + bool(cell & Wall.S)
#                                    + bool(cell & Wall.N))
#
#                 if wall_count == 3:
#                     candidates = []
#                     if ((cell & Wall.N) and y > 0 and (x, y - 1)
#                             not in (maze.locked_cells or visited)):
#                         candidates.append((x, y - 1, Wall.N, Wall.S))
#                     if ((cell & Wall.E) and x < maze.width - 1 and
#                             (x + 1, y) not in (maze.locked_cells
#                                                or visited)):
#                         candidates.append((x + 1, y, Wall.E, Wall.W))
#                     if ((cell & Wall.S) and y < maze.height - 1 and
#                             (x, y + 1) not in (maze.locked_cells
#                                                or visited)):
#                         candidates.append((x, y + 1, Wall.S, Wall.N))
#                     if ((cell & Wall.W) and x > 0 and (x - 1, y)
#                             not in (maze.locked_cells or visited)):
#                         candidates.append((x - 1, y, Wall.W, Wall.E))
#
#                     if candidates:
#                         nx, ny, wall1, wall2 = random.choice(candidates)
#                         maze.grid[y][x] &= ~wall1
#                         maze.grid[ny][nx] &= ~wall2
#                         visited.add((x, y))
