*This project has been created as part of the 42 curriculum by kdzwigal, kbartosz*

# A-Maze-ing

## Description

A-Maze-ing is a Python maze generator and visualizer. It creates a maze from a
configuration file, renders it in a terminal or with MiniLibX, solves it with a
shortest-path solver, and exports the result using the hexadecimal wall format
required by the project subject.

The reusable part is the `mazegen` package. It exposes several generation
algorithms, solvers, the maze model, and access to the generated wall bitmasks
and solution path.

Supported generation algorithms:

- `KRUSKAL`
- `PRIM`
- `WILSON`
- `BACKTRACKER`

Supported solvers:

- `BFS`
- `DFS`
- `ASTAR`

The generator supports two modes:

- `PERFECT=True`: generates a perfect maze without loops.
- `PERFECT=False`: removes additional walls to create a multi-route,
  Pac-Man-like board while preserving the closed-cell `42` pattern where the
  maze is large enough.

## Instructions

### Requirements

- Python 3.14 or newer, as declared in `pyproject.toml`.
- `uv` for the recommended environment and dependency workflow.
- A graphical Linux/X11 environment for the MLX backend.
- A terminal with enough space for the configured maze when using
  `DISPLAY_MODE=TERMINAL`.

The subject requires Python 3.10 or newer. This repository currently declares
`requires-python = ">=3.14"`, so Python 3.10--3.13 are not currently supported
by the package metadata.

### Installation

Create the virtual environment and install the project in editable mode:

```bash
make install
```

The equivalent commands are:

```bash
uv venv
uv pip install -e .
```

### Running the application

The required entry point is:

```bash
python3 a_maze_ing.py config.txt
```

The Makefile shortcut is:

```bash
make run
```

The application starts with the backend selected by `DISPLAY_MODE`, generates
the maze, solves it, and writes the result to `OUTPUT_FILE`.

### Debugging and cleanup

```bash
make debug
make clean
```

`make debug` starts the application through Python's `pdb`. `make clean`
removes local Python caches and the project virtual environment.

### Testing and linting

```bash
make test
make test-cov
make lint
make lint-strict
```

The tests use `pytest`. The analyzer integration test generates 100 mazes with
different deterministic seeds, exports each maze, and runs:

```bash
python3 maze_analyzer.py maze.txt
```

### Checking an exported maze

```bash
python3 maze_analyzer.py maze.txt
```

The analyzer checks shared-wall coherence, reachability, loops, dead ends,
corner and centre accessibility, and the `42` pattern. A successful process
exit code means that the file could be parsed and analyzed; the printed
`Verdict` describes whether the maze meets the playable-board thresholds.

## Configuration

`config.txt` contains one `KEY=VALUE` pair per line. Empty lines and lines
whose first non-whitespace character is `#` are ignored. Values may be
surrounded by whitespace.

Example:

```ini
WIDTH=30
HEIGHT=33
ENTRY=0,0
EXIT=29,32
OUTPUT_FILE=maze.txt
PERFECT=False
SEED=42
ALGORITHM=PRIM
SOLVER=ASTAR
ANIMATION=True
COLOR=green
DISPLAY_MODE=MLX
# WINDOW_WIDTH=1280
# WINDOW_HEIGHT=720
```

### Supported keys and validation

| Key | Type | Current validation and default |
|---|---|---|
| `WIDTH` | integer | Required; `4 <= WIDTH <= 863` |
| `HEIGHT` | integer | Required; `4 <= HEIGHT <= 455` |
| `ENTRY` | `x,y` | Required; must be inside the maze and outside locked `42` cells |
| `EXIT` | `x,y` | Required; same coordinate checks as `ENTRY` |
| `OUTPUT_FILE` | string | Required; non-empty, existing parent directory, writable path |
| `PERFECT` | boolean | Required; parsed by Pydantic |
| `SEED` | integer or empty | Default `None`; an empty value becomes `None` |
| `ALGORITHM` | enum | Default `KRUSKAL`; `KRUSKAL`, `PRIM`, `WILSON`, `BACKTRACKER` |
| `SOLVER` | enum | Default `BFS`; `BFS`, `DFS`, `ASTAR` |
| `ANIMATION` | boolean | Default `True` |
| `COLOR` | string | Default `green`; length 1--80 |
| `DISPLAY_MODE` | string | Default `MLX`; runtime supports `MLX` and `TERMINAL` |
| `WINDOW_WIDTH` | integer | Optional; `640 <= value <= 7680` |
| `WINDOW_HEIGHT` | integer | Optional; `480 <= value <= 4320` |

`ENTRY` and `EXIT` use Cartesian coordinates `(x, y)`, with `(0, 0)` at the
top-left. The parser converts the comma-separated value to a two-item tuple
before Pydantic validation. For MLX and terminal modes, additional
screen-dependent size limits are checked.

### Configuration audit against the subject

The parser correctly handles comments, blank lines, typed coordinates,
integer window dimensions, Pydantic validation, coordinate bounds, identical
entry/exit rejection, locked `42` cells, output-path checks, and display-size
limits. Invalid file access and validation errors are converted into clear
`ValueError` messages by `read_config`.

The following differences from the subject remain:

1. A non-empty line without `=` is silently skipped by `read_and_parse`
   instead of being rejected as malformed syntax.
2. Unknown keys are collected and ignored rather than rejected.
3. `DISPLAY_MODE` accepts arbitrary strings in the model; the backend registry
   later falls back to `TERMINAL` for an unknown value.
4. The subject asks for a `LICENSE.md` file. The repository currently provides
   an MIT license in `LICENSE` instead.
5. `pyproject.toml` requires Python 3.14 even though the subject baseline is
   Python 3.10 or newer.

The six mandatory keys are now represented as required Pydantic fields. If any
of them is missing, configuration loading fails with a `Field required`
validation error.

## Output format

The exporter writes one hexadecimal digit per cell, one row per line. The
closed-wall bit mapping is:

| Bit | Direction |
|---:|---|
| 0 (`1`) | North |
| 1 (`2`) | East |
| 2 (`4`) | South |
| 3 (`8`) | West |

A set bit means that the wall is closed. After the grid, the file contains a
blank line followed by:

1. the entry coordinates;
2. the exit coordinates;
3. the shortest path as `N`, `E`, `S`, and `W`.

## Interactive controls

The exact key map is defined in `app/keys.py`. The main controls are:

| Key | Action |
|---|---|
| `R` | Regenerate the maze |
| `N` | Generate a new random seed |
| `K` | Enter a seed manually |
| `A` | Cycle generation algorithm |
| `S` | Cycle solver, including manual mode |
| `H` | Show or hide the solution path |
| `C` | Cycle wall palette |
| `P` | Toggle perfect/imperfect mode |
| `Space` | Pause |
| `End` | Skip generation/solving animation |
| `Tab` | Change arrow interaction mode |
| Arrow keys | Move in the selected mode |
| `Q` or `Esc` | Quit |
| `+` / `-` | Change animation speed |

The terminal and MLX backends render walls, entry, exit, the solution path,
and the locked `42` cells.

## Reusable `mazegen` API

The package can be imported independently of the visual application:

```python
import mazegen

maze = mazegen.generate_maze(
    width=10,
    height=10,
    m_entry=(0, 0),
    m_exit=(9, 9),
    algorithm="kruskal",
    perfect=True,
    seed=42,
)

path = mazegen.solve_maze(maze, algorithm="bfs")
walls_n, walls_e, walls_s, walls_w = maze.get_walls()

print(path)
print(walls_n, walls_e, walls_s, walls_w)
```

`Maze` exposes `width`, `height`, `m_entry`, `m_exit`, `path`, and the four
wall bitmasks through `get_walls()`. For animated use, applications can use
`create_stepping_generator()` and `create_stepping_solver()`.

Build the reusable package from the repository root with:

```bash
uv build --wheel --out-dir .
```

The package metadata is in `pyproject.toml`, and the build output is named
`mazegen-<version>-*.whl`.

## Project structure

```text
a_maze_ing.py              Application entry point
config.txt                 Default configuration
app/                       Configuration, engine, rendering, and export code
mazegen/                   Reusable maze and solver package
maze_analyzer.py           Export-file validation and reporting tool
tests/                     Unit, property, and integration tests
Makefile                   Installation, execution, lint, test, and build tasks
LICENSE                    MIT reuse and distribution license
```

## Resources

- The project specification: `amazeing.pdf`, version 2.3.
- Python documentation: <https://docs.python.org/3/>
- Pydantic validation documentation: <https://docs.pydantic.dev/>
- Pytest documentation: <https://docs.pytest.org/>
- `uv` documentation: <https://docs.astral.sh/uv/>
- MiniLibX documentation and examples used by the local MLX package.
- Classic maze-generation algorithms: Prim's algorithm, Kruskal's algorithm,
  Wilson's algorithm, and recursive backtracking.

AI was used for repetitive engineering support: exploring the repository,
comparing implementation details with the assignment specification, designing
test coverage for multiple seeds, and drafting documentation. All generated
changes and audit statements should be reviewed and understood by the project
authors before evaluation.

## License

This project is distributed under the MIT License. See `LICENSE`.
