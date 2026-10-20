# example_usage.py
import mazegen


def main() -> None:
    print("--- 1. Generating an Imperfect Maze via .whl API ---")

    # Generate a 10x10 maze using Kruskal's algorithm
    # Setting perfect=False automatically applies your ImperfectGenerator decorator
    maze_instance = mazegen.generate_maze(
        width=10,
        height=10,
        m_entry=(0, 0),
        m_exit=(9, 9),
        algorithm="kruskal",  # Case-insensitive thanks to .upper()
        perfect=False,
        seed=42
    )

    print(
        f"Successfully generated a maze of size: {maze_instance.width}x{maze_instance.height}")

    # Access the internal wall bitmasks (Required requirement: Accessing the generated structure)
    walls_n, walls_e, walls_s, walls_w = maze_instance.get_walls()
    print(f"North walls bitmask: {walls_n}")
    print(f"East walls bitmask:  {walls_e}")

    print("\n--- 2. Solving the Generated Maze ---")

    # Find the shortest path using the Breadth-First Search solver
    shortest_path = mazegen.solve_maze(maze_instance, algorithm="bfs")

    print(
        f"Path found from entry {maze_instance.m_entry} to exit {maze_instance.m_exit}:")
    print(shortest_path)

    # Verify the coordinates are also stored in the maze object itself
    assert maze_instance.path == shortest_path
    print(f"Number of cells in the solution path: {len(maze_instance.path)}")


if __name__ == "__main__":
    main()