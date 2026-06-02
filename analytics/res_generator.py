"""Generate README stats table from assets/data and inject between marker comments."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cleaners.registry import get_pipeline_label

ROOT_DIR = _REPO_ROOT / "assets" / "data"
README_PATH = _REPO_ROOT / "README.md"
INJECT_MARKER = "<!-- INJECT STATS-->"

# Legacy paths (unused by table generation; kept for optional solver checks)
PUZZLES_DIR = Path("../Puzzles")
COMMON_PARSERS_DIR = PUZZLES_DIR / "Common" / "Parser" / "PuzzleParsers"


def parse_problem_size(problem_str: str) -> tuple[int, int] | None:
    """Parse m n from the first line of problem text."""
    if not problem_str:
        return None
    first_line = problem_str.strip().split("\n")[0].strip()
    tokens = first_line.split()
    if len(tokens) < 2:
        return None
    try:
        return int(tokens[0]), int(tokens[1])
    except (ValueError, IndexError):
        return None


def get_size_stats(puzzles_dict: dict) -> tuple[str, str]:
    """Return (size_range, distinct_count), e.g. ('4x4~17x17', '12') or ('-', '-')."""
    sizes = []
    for puzzle_data in puzzles_dict.values():
        dims = parse_problem_size(puzzle_data.get("problem", ""))
        if dims is not None:
            sizes.append(dims)

    if not sizes:
        return "-", "-"

    min_dims = min(sizes, key=lambda d: d[0] * d[1])
    max_dims = max(sizes, key=lambda d: d[0] * d[1])
    min_str = f"{min_dims[0]}x{min_dims[1]}"
    max_str = f"{max_dims[0]}x{max_dims[1]}"
    size_range = min_str if min_dims == max_dims else f"{min_str}~{max_str}"
    distinct_count = len({dims for dims in sizes})
    return size_range, str(distinct_count)


def check_solver_files(puzzle_name: str) -> str:
    """Return checkmark if solver and parser files exist (optional tooling)."""
    solver_path = PUZZLES_DIR / f"{puzzle_name}Solver.py"
    parser_path = COMMON_PARSERS_DIR / f"{puzzle_name}Parser.py"
    if solver_path.exists() and parser_path.exists():
        return "✅"
    return "❌"


def collect_table_rows() -> tuple[list[list[str]], int, int]:
    """Scan assets/data and build table body rows plus totals."""
    if not ROOT_DIR.exists():
        raise FileNotFoundError(f"Data directory not found: {ROOT_DIR}")

    subdirs = sorted((d for d in ROOT_DIR.iterdir() if d.is_dir()), key=lambda d: d.name)
    table_data: list[list[str]] = []
    total_problems = 0
    total_solutions = 0

    for idx, puzzle_dir in enumerate(subdirs, 1):
        puzzle_name = puzzle_dir.name
        merged_path = puzzle_dir / f"{puzzle_name}_dataset.json"

        p_count = "-"
        s_count = "-"
        size_range = "-"
        spec_count = "-"

        if merged_path.exists():
            try:
                with open(merged_path, encoding="utf-8") as f:
                    data = json.load(f)
                puzzles_data = data.get("data", {})
                count = data.get("count", len(puzzles_data))
                count_sol = data.get("count_sol", 0)
                p_count = str(count)
                s_count = str(count_sol)
                total_problems += count
                total_solutions += count_sol
                size_range, spec_count = get_size_stats(puzzles_data)
            except Exception as e:
                print(f"Warning: {merged_path}: {e}", file=sys.stderr)

        table_data.append(
            [
                str(idx),
                puzzle_name,
                str(p_count),
                str(s_count),
                size_range,
                spec_count,
                get_pipeline_label(puzzle_name),
            ]
        )

    return table_data, total_problems, total_solutions


def format_markdown_table(table_data: list[list[str]], total_problems: int, total_solutions: int) -> str:
    """Return markdown table lines (no inject markers)."""
    headers = [
        "No.",
        "Puzzle Name",
        "#. prob.",
        "#. sols.",
        "Size Range",
        "#. specs",
        "Pipeline",
    ]
    lines = [
        f"| {' | '.join(headers)} |",
        f"| {' | '.join(['---'] * len(headers))} |",
    ]
    for row in table_data:
        lines.append(f"| {' | '.join(row)} |")
    lines.append(
        f"| | **Total** | **{total_problems}** | **{total_solutions}** | - | - | - |"
    )
    return "\n".join(lines)


def build_markdown_table() -> str:
    table_data, total_problems, total_solutions = collect_table_rows()
    return format_markdown_table(table_data, total_problems, total_solutions)


def inject_readme(readme_path: Path = README_PATH) -> None:
    """Replace content between INJECT markers in README with a fresh stats table."""
    text = readme_path.read_text(encoding="utf-8")
    start = text.find(INJECT_MARKER)
    if start == -1:
        raise ValueError(f"Opening marker not found in {readme_path}: {INJECT_MARKER!r}")

    after_open = start + len(INJECT_MARKER)
    end = text.find(INJECT_MARKER, after_open)
    if end == -1:
        raise ValueError(f"Closing marker not found in {readme_path}: {INJECT_MARKER!r}")

    table = build_markdown_table()
    new_block = f"{INJECT_MARKER}\n{table}\n{INJECT_MARKER}"
    readme_path.write_text(text[:start] + new_block + text[end + len(INJECT_MARKER) :], encoding="utf-8")
    try:
        label = str(readme_path.relative_to(_REPO_ROOT))
    except ValueError:
        label = str(readme_path)
    print(f"Updated {label} ({len(table.splitlines())} table lines)")


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate README puzzle stats table.")
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Print table to stdout only (do not modify README)",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=README_PATH,
        help=f"README path for injection (default: {README_PATH.relative_to(_REPO_ROOT)})",
    )
    args = parser.parse_args()

    try:
        if args.stdout:
            print(build_markdown_table())
        else:
            inject_readme(args.readme.resolve())
    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
