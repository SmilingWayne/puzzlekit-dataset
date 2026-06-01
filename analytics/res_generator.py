import json
from pathlib import Path

# Set data root directory path
ROOT_DIR = Path("./assets/data")

# Directories to check for solver/parser/verifier files
PUZZLES_DIR = Path("../Puzzles")
COMMON_PARSERS_DIR = PUZZLES_DIR / "Common" / "Parser" / "PuzzleParsers"

def parse_problem_size(problem_str):
    """Parse m n from the first line of problem text. Returns (m, n) or None."""
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


def get_size_stats(puzzles_dict):
    """
    Collect grid sizes from all problems.
    Returns (size_range, distinct_count): e.g. ("4x4–17x17", 12) or ("-", "-").
    Min/max compared by area (m * n).
    """
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

def check_solver_files(puzzle_name):
    """
    Check if all required solver files exist for a puzzle.
    Returns ✅ if all exist, ❌ otherwise.
    """
    # Check for solver file
    solver_path = PUZZLES_DIR / f"{puzzle_name}Solver.py"
    
    # Check for parser file
    parser_path = COMMON_PARSERS_DIR / f"{puzzle_name}Parser.py"
    
    # Check if all files exist
    if solver_path.exists() and parser_path.exists():
        return "✅"
    return "❌"

def generate_markdown_table():
    if not ROOT_DIR.exists():
        print(f"Error: Directory '{ROOT_DIR}' not found.")
        return

    # Get all subdirectories and sort
    subdirs = [d for d in ROOT_DIR.iterdir() if d.is_dir()]
    subdirs.sort(key=lambda x: x.name)  # Sort alphabetically

    table_data = []  # Store data for each row
    total_problems = 0
    total_solutions = 0  # Now equals total_problems since all puzzles have solution slots

    # Table headers
    headers = ["No.", "Puzzle Name", "#. prob.", "#. sols.", "Size Range", "#. specs"]
    
    # Traverse each puzzle directory
    for idx, puzzle_dir in enumerate(subdirs, 1):
        puzzle_name = puzzle_dir.name
        
        # Build merged file path
        merged_path = puzzle_dir / f"{puzzle_name}_dataset.json"

        # Initialize row variables
        p_count = "-"
        s_count = "-"
        size_range = "-"
        spec_count = "-"

        # Process merged JSON
        if merged_path.exists():
            try:
                with open(merged_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Get count from top-level field or calculate from data
                    puzzles_data = data.get("data", {})
                    count = data.get("count", len(puzzles_data))
                    count_sol = data.get("count_sol", 0)
                    
                    p_count = count
                    s_count = count_sol
                    total_problems += count
                    total_solutions += count_sol
                    
                    size_range, spec_count = get_size_stats(puzzles_data)
            except Exception as e:
                print(f"⚠️  Error processing {merged_path}: {e}", file=sys.stderr)
                pass

        table_data.append([
            str(idx), 
            puzzle_name, 
            str(p_count), 
            str(s_count), 
            size_range,
            spec_count,
        ])

    # --- Generate Markdown Output ---
    print(f"| {' | '.join(headers)} |")
    print(f"| {' | '.join(['---'] * len(headers))} |")

    # Print data rows
    for row in table_data:
        print(f"| {' | '.join(row)} |")

    # Print summary row
    print(f"| | **Total** | **{total_problems}** | **{total_solutions}** | - | - |")

if __name__ == "__main__":
    import sys
    generate_markdown_table()