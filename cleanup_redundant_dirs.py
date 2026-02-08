#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Directly remove ALL 'problems' and 'solutions' directories under assets/data/<puzzle_type>/
This is a destructive operation - includes safety confirmation and dry-run mode.
"""

import sys
from pathlib import Path
import shutil
import argparse

def remove_redundant_dirs(root_dir: Path = Path("assets/data"), dry_run: bool = True):
    """Remove problems/ and solutions/ directories from all puzzle types."""
    if not root_dir.exists():
        print(f"❌ Error: Directory not found: {root_dir.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    if not root_dir.is_dir():
        print(f"❌ Error: Not a directory: {root_dir.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    # Get all puzzle type directories
    puzzle_dirs = sorted([d for d in root_dir.iterdir() if d.is_dir()])
    if not puzzle_dirs:
        print(f"⚠️  No puzzle directories found in {root_dir.absolute()}")
        return 0, 0
    
    print(f"🔍 Found {len(puzzle_dirs)} puzzle directories in {root_dir.absolute()}\n")
    
    total_removed = 0
    total_failed = 0
    skipped = []
    
    for i, puzzle_dir in enumerate(puzzle_dirs, 1):
        print(f"[{i}/{len(puzzle_dirs)}] Processing: {puzzle_dir.name} ... ", end='', flush=True)
        
        problems_dir = puzzle_dir / "problems"
        solutions_dir = puzzle_dir / "solutions"
        
        # Check if anything needs removal
        dirs_to_remove = []
        if problems_dir.exists() and problems_dir.is_dir():
            dirs_to_remove.append(problems_dir)
        if solutions_dir.exists() and solutions_dir.is_dir():
            dirs_to_remove.append(solutions_dir)
        
        if not dirs_to_remove:
            print("✓ Nothing to remove")
            continue
        
        # Perform removal (or dry-run)
        success_count = 0
        for dir_path in dirs_to_remove:
            try:
                rel_path = dir_path.resolve().relative_to(Path.cwd())
            except ValueError:
                rel_path = str(dir_path)
            
            if dry_run:
                print(f"\n  🗑️  [DRY RUN] Would remove: {rel_path}", end='')
            else:
                try:
                    shutil.rmtree(dir_path)
                    print(f"\n  ✅ Removed: {rel_path}", end='')
                    success_count += 1
                except Exception as e:
                    print(f"\n  ❌ Failed to remove {rel_path}: {e}", file=sys.stderr)
                    total_failed += 1
        
        if dirs_to_remove:
            total_removed += success_count
            status = "✅ REMOVED" if not dry_run else "✅ [DRY RUN] MARKED FOR REMOVAL"
            print(f"\n  → {status} ({len(dirs_to_remove)} directories)")
    
    # Summary
    print("\n" + "="*60)
    print("REMOVAL SUMMARY")
    print("="*60)
    print(f"Puzzle types scanned:    {len(puzzle_dirs)}")
    if not dry_run:
        print(f"Directories removed:     {total_removed}")
        print(f"Removal failures:        {total_failed}")
        if total_removed > 0:
            print("\n✅ Cleanup completed successfully.")
        else:
            print("\nℹ️  No directories were removed.")
    else:
        print(f"Directories to remove:   {total_removed} (in dry run)")
        print("\n💡 This was a DRY RUN. No files were actually deleted.")
        print("   Run with --no-dry-run to perform actual removal.")
    
    return total_removed, total_failed

def main():
    parser = argparse.ArgumentParser(
        description="Remove ALL problems/ and solutions/ directories from puzzle datasets"
    )
    parser.add_argument("--no-dry-run", action="store_true", 
                       help="Perform actual deletion (default is dry run)")
    args = parser.parse_args()
    
    dry_run = not args.no_dry_run
    
    if dry_run:
        print("🛡️  DRY RUN MODE (no files will be deleted)\n")
        print("This script will scan for and report all 'problems/' and 'solutions/'")
        print("directories that would be removed. No actual deletion will occur.\n")
    else:
        print("⚠️  ACTUAL DELETION MODE\n")
        print("This will PERMANENTLY DELETE all 'problems/' and 'solutions/' directories")
        print("under assets/data/<puzzle_type>/")
        print("\n⚠️  WARNING: This operation cannot be undone!")
        confirm = input("\nType 'DELETE' to confirm: ").strip()
        if confirm != "DELETE":
            print("\n❌ Operation aborted by user.")
            sys.exit(1)
        print()
    
    try:
        remove_redundant_dirs(dry_run=dry_run)
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()