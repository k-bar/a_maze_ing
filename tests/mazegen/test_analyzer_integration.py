import re
import shutil
import subprocess
from pathlib import Path

from app.export_func import export_to_file
from mazegen import create_stepping_generator, solve_maze


def test_generated_mazes_are_accepted_by_analyzer(tmp_path: Path) -> None:
    project_root = Path(__file__).parents[2]
    analyzer_name = "maze_analyzer.py"
    maze_file_name = "maze.txt"

    shutil.copy2(
        project_root / analyzer_name,
        tmp_path / analyzer_name,
    )

    bonus_grade_count = 0
    dead_ends_total = 0
    non_bonus_count = 0

    for seed in range(100):
        generator = create_stepping_generator(
            algorithm_name="PRIM",
            width=3,
            height=3,
            m_entry=(0, 0),
            m_exit=(2, 2),
            perfect=False,
            seed=seed,
        )
        while generator.step() is not None:
            pass

        maze = generator.maze
        solve_maze(maze, algorithm="BFS")
        export_to_file(maze, str(tmp_path / maze_file_name))

        result = subprocess.run(
            ["python3", analyzer_name, maze_file_name],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            check=False,
        )

        assert result.returncode == 0, (
            f"Analyzer failed for seed={seed}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )

        verdict_line = next(
            (
                line.removeprefix("Verdict:").strip()
                for line in result.stdout.splitlines()
                if line.startswith("Verdict:")
            ),
            "",
        )

        if "no real dead-end -> bonus-grade" in verdict_line:
            bonus_grade_count += 1
            continue

        non_bonus_count += 1
        match = re.search(r"Dead-ends\s*:\s*(\d+)\s+real", result.stdout)
        assert match is not None, (
            f"Could not read real dead-ends for seed={seed}\n"
            f"{result.stdout}"
        )
        dead_ends_total += int(match.group(1))

    print(
        f"\nBonus-grade: {bonus_grade_count}/100\n"
        f"Non-bonus mazes: {non_bonus_count}/100\n"
        f"Real dead-ends in non-bonus mazes: {dead_ends_total}"
    )
