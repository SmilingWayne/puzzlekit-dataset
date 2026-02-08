import os
import json
from pathlib import Path

# Set data root directory path
ROOT_DIR = Path("../assets/data")

# Directories to check for solver/parser/verifier files
PUZZLES_DIR = Path("../Puzzles")
CRAWLERS_DIR = Path("../crawlers")
COMMON_PARSERS_DIR = PUZZLES_DIR / "Common" / "Parser" / "PuzzleParsers"

def get_max_size(puzzles_dict):
    """
    Traverse puzzles dictionary, parse dimensions from first line, 
    return max size string (compared by area).
    Returns "-" if unable to get dimensions.
    """
    max_area = -1
    max_size_str = "-"

    for puzzle_data in puzzles_dict.values():
        problem_str = puzzle_data.get("problem", "")
        if not problem_str:
            continue

        # Get first line
        first_line = problem_str.strip().split('\n')[0].strip()
        tokens = first_line.split()

        # Try to read first two numbers
        if len(tokens) >= 2:
            try:
                dim1 = int(tokens[0])
                dim2 = int(tokens[1])
                area = dim1 * dim2
                
                if area > max_area:
                    max_area = area
                    max_size_str = f"{dim1}x{dim2}"
            except (ValueError, IndexError):
                continue
    
    return max_size_str

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

def check_crawler_file(puzzle_name):
    """
    Check if crawler file exists for a puzzle.
    Returns ✅ if exists, ❌ otherwise.
    """
    crawler_path = CRAWLERS_DIR / f"{puzzle_name}Crawler.py"
    
    if crawler_path.exists():
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
    headers = ["No.", "Puzzle Name", "Problems", "Solutions", "Max Size", "crawler?"]
    
    # Traverse each puzzle directory
    for idx, puzzle_dir in enumerate(subdirs, 1):
        puzzle_name = puzzle_dir.name
        
        # Build merged file path
        merged_path = puzzle_dir / f"{puzzle_name}_dataset.json"

        # Initialize row variables
        p_count = "-"
        s_count = "-"
        max_size = "-"
        crawler_status = "❌"

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
                    s_count = count_sol  # In new format, all puzzles have solution slots (may be empty strings)
                    total_problems += count
                    total_solutions += count_sol
                    
                    # Calculate max size
                    max_size = get_max_size(puzzles_data)
            except Exception as e:
                print(f"⚠️  Error processing {merged_path}: {e}", file=sys.stderr)
                pass

        # Check crawler file status
        try:
            crawler_status = check_crawler_file(puzzle_name)
        except Exception as e:
            pass

        table_data.append([
            str(idx), 
            puzzle_name, 
            str(p_count), 
            str(s_count), 
            max_size, 
            crawler_status
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