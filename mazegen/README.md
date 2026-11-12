*This project has been created as part of the 42 curriculum by kdzwigal, kbartosz.*

# mazegen — Standalone Maze Generation & Solving Library

## Description

**`mazegen`** is a zero-dependency Python library designed for generating, manipulating, and solving 2D grid mazes. Built around flat 1D bitmask representations for high memory efficiency and speed, it supports both instant generation/solving and step-by-step generator iterators for real-time visualization.

### Key Features
* **Multiple Generation Algorithms:** Kruskal's Algorithm, Prim's Algorithm, Recursive Backtracker (DFS), and Wilson's Algorithm (Loop-Erased Random Walk).
* **Imperfect Maze Support:** Post-processing decorator (`ImperfectGenerator`) that removes dead ends to create loops while strictly preventing open `3x3` empty rooms.
* **Built-in Pathfinding Solvers:** A* Search (`ASTAR`), Breadth-First Search (`BFS`), and Depth-First Search (`DFS`).
* **Embedded Pattern Support:** Automatic locking and preservation of the central `"42"` glyph on grids of size `8x7` or larger.
* **Step-by-Step Execution:** Generator-based stepping API (`step()`) allowing frame-by-frame animation in any frontend (Terminal, MLX, Web, etc.).

---

## Instructions

### Building the Wheel Package (`.whl`)
From the project root directory, build the standalone distribution package using `uv` or standard `build`:

```bash
uv build
# or via Makefile:
make build
```

This produces a `.whl` archive (e.g., `dist/mazegen-0.1.0-py3-none-any.whl`).

### Installation
Install the built wheel package into any Python 3.10+ environment:

```bash
pip install dist/mazegen-0.1.0-py3-none-any.whl
# or using uv:
uv pip install dist/mazegen-0.1.0-py3-none-any.whl
```

---

## Usage & API Reference

### 1. Instant Maze Generation & Solving
Use `generate_maze()` to create a completed `Maze` object in a single call, and `solve_maze()` to compute the path between `ENTRY` and `EXIT`.

```python
from mazegen import generate_maze, solve_maze

# Generate a 20x15 perfect maze using Prim's algorithm
maze = generate_maze(
    algorithm="PRIM",
    width=20,
    height=15,
    m_entry=(0, 0),
    m_exit=(19, 14),
    perfect=True,
    seed=42,
)

# Solve the maze using A*
path = solve_maze(maze, solver="ASTAR")
print(f"Path length: {len(path)} steps")
print(f"Coordinates: {path[:5]}...")
```

### 2. Step-by-Step Generation & Solving (For Animations)
Use `create_stepping_generator()` and `create_stepping_solver()` to advance algorithms one cell at a time. Each `.step()` call yields `(x, y, Direction)` until completion (`None`).

```python
from mazegen import create_stepping_generator, create_stepping_solver

generator = create_stepping_generator(
    algorithm_name="BACKTRACKER",
    width=15,
    height=15,
    m_entry=(0, 0),
    m_exit=(14, 14),
    perfect=False,  # Creates loops without open 3x3 rooms
    seed=123,
)

# Advance generation step by step
while (step_info := generator.step()) is not None:
    x, y, direction = step_info
    # Update your UI / canvas here

maze = generator.maze

# Advance solver step by step
solver = create_stepping_solver(solver_name="BFS", maze=maze)
while (visit_info := solver.step()) is not None:
    vx, vy, v_dir = visit_info
    # Render visited frontier here

print("Final solution:", maze.path)
```

### 3. Inspecting Walls & Maze Structure
The `Maze` object stores wall states as compact integer bitmasks (`walls_n`, `walls_e`, `walls_s`, `walls_w`), where bit index `y * width + x` represents cell `(x, y)`.

```python
from mazegen import generate_maze, get_available_algorithms, get_available_solvers

print("Algorithms:", get_available_algorithms())  # ['KRUSKAL', 'PRIM', 'BACKTRACKER', 'WILSON']
print("Solvers:", get_available_solvers())        # ['ASTAR', 'BFS', 'DFS']

maze = generate_maze("KRUSKAL", width=10, height=10, seed=7)
wn, we, ws, ww = maze.get_walls()

# Check walls for cell (x=2, y=3)
x, y = 2, 3
cell_bit = 1 << (y * maze.width + x)

has_north_wall = bool(wn & cell_bit)
has_east_wall = bool(we & cell_bit)
has_south_wall = bool(ws & cell_bit)
has_west_wall = bool(ww & cell_bit)

print(f"Cell ({x},{y}) walls -> N:{has_north_wall}, E:{has_east_wall}, S:{has_south_wall}, W:{has_west_wall}")
print("Locked '42' cells:", maze.locked_cells)
```

---

## Resources

### Classic References
* [Jamis Buck — Maze Generation Algorithms (The Buckblog)](https://jamisbuck.org) — Detailed visual explanations of Kruskal's, Prim's, Recursive Backtracker, and Wilson's algorithms.
* [Wikipedia - Maze generation algorithm](https://en.wikipedia.org/wiki/Maze_generation_algorithm) — descriptions of different maze generators.

### AI Usage Disclosure
AI tools were used during the development of `mazegen` for the following specific tasks:
* **Performance Optimization:** Refactoring 2D coordinate tuple operations into flat 1D integer indexing (`y * width + x`) and bitmask shifts to eliminate memory bottlenecks on large grids.
* **Algorithm Verification & Edge Cases:** Designing property-based `pytest` suites to detect and prevent open `3x3` rooms and remaining dead ends in `ImperfectGenerator`.
