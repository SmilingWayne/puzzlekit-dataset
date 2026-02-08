#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Merge puzzle problems and solutions into unified dataset JSON files.
Output format:
{
  "count": <total puzzles>,
  "count_sol": <puzzles with non-empty solutions>,
  "name": "<puzzle_type>",
  "data": {
    "<puzzle_id>": {
      "problem": "<str>",
      "solution": "<str>",  # May be empty string ""
      "source": "<str>",
      "info": ""
    },
    ...
  }
}
"""

import os
import json
import sys
from pathlib import Path
from typing import Dict, Any, Tuple


def load_json_file(filepath: Path) -> Dict[str, Any]:
    """Safely load a JSON file with error handling."""
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in {filepath}: {e}")
    except Exception as e:
        raise RuntimeError(f"Error reading {filepath}: {e}")


def merge_puzzle_data(problems_data: Dict[str, Any], solutions_data: Dict[str, Any]) -> Tuple[Dict[str, Any], int]:
    """
    Merge problems and solutions into unified structure.
    Returns: (merged_data_dict, count_of_non_empty_solutions)
    """
    puzzles_dict = problems_data.get('puzzles', {})
    solutions_dict = solutions_data.get('solutions', {}) if solutions_data else {}
    
    merged = {}
    non_empty_sol_count = 0
    
    for pid, pinfo in puzzles_dict.items():
        problem_str = pinfo.get('problem', '')
        source_problem = (pinfo.get('source') or '').strip()
        
        sinfo = solutions_dict.get(pid, {})
        solution_str = sinfo.get('solution', '')
        source_solution = (sinfo.get('source') or '').strip()
        
        # Determine source: prefer problem's source, fallback to solution's
        source = source_problem if source_problem else source_solution
        
        # Count non-empty solutions (strip whitespace to handle "   " cases)
        if solution_str.strip():
            non_empty_sol_count += 1
        
        merged[pid] = {
            "problem": problem_str,
            "solution": solution_str,
            "source": source,
            "info": ""
        }
    
    return merged, non_empty_sol_count


def process_puzzle_type(puzzle_dir: Path) -> Tuple[bool, str, int, int]:
    """
    Process a single puzzle type directory.
    Returns: (success, message, total_count, solved_count)
    """
    puzzle_type = puzzle_dir.name
    
    # Check required directories
    problems_dir = puzzle_dir / 'problems'
    solutions_dir = puzzle_dir / 'solutions'
    
    if not problems_dir.is_dir():
        return False, f"SKIPPED: 'problems' directory not found in {puzzle_type}", 0, 0
    
    # Locate JSON files
    problems_json = problems_dir / f"{puzzle_type}_puzzles.json"
    solutions_json = solutions_dir / f"{puzzle_type}_solutions.json" if solutions_dir.is_dir() else None
    
    # Load problems (mandatory)
    try:
        problems_data = load_json_file(problems_json)
    except Exception as e:
        return False, f"ERROR loading problems for {puzzle_type}: {e}", 0, 0
    
    # Load solutions (optional)
    solutions_data = None
    if solutions_json and solutions_json.exists():
        try:
            solutions_data = load_json_file(solutions_json)
        except Exception as e:
            print(f"  ⚠️  Warning: Failed to load solutions for {puzzle_type}: {e}", file=sys.stderr)
    
    # Merge data
    try:
        merged_data, solved_count = merge_puzzle_data(problems_data, solutions_data)
    except Exception as e:
        return False, f"ERROR merging data for {puzzle_type}: {e}", 0, 0
    
    # Build output structure with new count_sol field
    output = {
        "count": len(merged_data),
        "count_sol": solved_count,  # NEW: count of puzzles with non-empty solutions
        "name": puzzle_type,
        "data": merged_data
    }
    
    # Write output file with NEW naming convention
    output_path = puzzle_dir / f"{puzzle_type}_dataset.json"  # CHANGED: _dataset.json
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output, f, indent=2, ensure_ascii=False)
    except Exception as e:
        return False, f"ERROR writing output for {puzzle_type}: {e}", 0, 0
    
    return True, f"SUCCESS: {puzzle_type} → {len(merged_data)} puzzles ({solved_count} with solutions)", len(merged_data), solved_count


def main():
    base_dir = Path('assets') / 'data'
    
    if not base_dir.exists():
        print(f"ERROR: Base directory not found: {base_dir.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    if not base_dir.is_dir():
        print(f"ERROR: Path is not a directory: {base_dir.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    print(f"🔍 Scanning puzzle types in: {base_dir.absolute()}\n")
    
    puzzle_dirs = sorted([d for d in base_dir.iterdir() if d.is_dir()])
    total_processed = 0
    total_skipped = 0
    total_puzzles = 0
    total_solved = 0
    errors = []
    
    for i, puzzle_dir in enumerate(puzzle_dirs, 1):
        print(f"[{i}/{len(puzzle_dirs)}] Processing: {puzzle_dir.name} ... ", end='', flush=True)
        success, message, count, solved = process_puzzle_type(puzzle_dir)
        
        if success:
            print("✅")
            total_processed += 1
            total_puzzles += count
            total_solved += solved
        else:
            print("❌")
            print(f"    → {message}")
            if "ERROR" in message:
                errors.append((puzzle_dir.name, message))
            total_skipped += 1
    
    # Summary report
    print("\n" + "="*70)
    print("MERGE SUMMARY")
    print("="*70)
    print(f"Total puzzle types found:   {len(puzzle_dirs)}")
    print(f"Successfully processed:     {total_processed}")
    print(f"Skipped/Failed:             {total_skipped}")
    print(f"\n📊 TOTAL STATISTICS")
    print(f"   Total puzzles:           {total_puzzles}")
    print(f"   Puzzles with solutions:  {total_solved}")
    print(f"   Solution coverage:       {(total_solved/total_puzzles*100):.1f}%" if total_puzzles else "   Solution coverage:       N/A")
    
    if errors:
        print(f"\n⚠️  ERRORS DETECTED ({len(errors)}):")
        for name, msg in errors:
            print(f"  • {name}: {msg}")
        sys.exit(1)
    else:
        print("\n✅ All operations completed successfully.")
        print(f"\n💡 Dataset files saved as '<puzzle_type>_dataset.json' in each puzzle directory.")
        print("   Original data remains untouched.")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Process interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)