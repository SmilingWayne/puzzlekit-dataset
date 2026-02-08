#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Safely remove all previously generated *_merged.json files.
Fixed: 
  1. Namespace access error (use args.no_dry_run instead of args['no_dry_run'])
  2. Path resolution issue (use .resolve() for cross-platform compatibility)
  3. Parameter logic clarity (default=dry-run, --no-dry-run for actual deletion)
"""

import sys
from pathlib import Path
import argparse

def find_merged_files(root_dir: Path) -> list[Path]:
    """Find all *_merged.json files under assets/data."""
    if not root_dir.exists():
        print(f"❌ Error: Directory not found: {root_dir.absolute()}", file=sys.stderr)
        sys.exit(1)
    
    merged_files = []
    for puzzle_dir in root_dir.iterdir():
        if puzzle_dir.is_dir():
            pattern = f"{puzzle_dir.name}_merged.json"
            merged_path = puzzle_dir / pattern
            if merged_path.exists():
                merged_files.append(merged_path)
    
    return sorted(merged_files)

def delete_files(file_paths: list[Path], dry_run: bool = True) -> tuple[int, int]:
    """Delete files with safety checks."""
    deleted = 0
    failed = 0
    
    if not file_paths:
        print("✅ No *_merged.json files found to delete.")
        return 0, 0
    
    print(f"🔍 Found {len(file_paths)} *_merged.json files to {'delete' if not dry_run else 'preview'}:\n")
    
    for i, fp in enumerate(file_paths, 1):
        # FIX: 统一转换为绝对路径后再计算相对路径
        try:
            rel_path = fp.resolve().relative_to(Path.cwd())
        except ValueError:
            # 回退方案：直接使用字符串表示
            rel_path = str(fp)
            
        if dry_run:
            print(f"[{i}/{len(file_paths)}] 🗑️  [DRY RUN] Would delete: {rel_path}")
        else:
            try:
                fp.unlink()
                print(f"[{i}/{len(file_paths)}] ✅ Deleted: {rel_path}")
                deleted += 1
            except Exception as e:
                print(f"[{i}/{len(file_paths)}] ❌ Failed to delete {rel_path}: {e}", file=sys.stderr)
                failed += 1
    
    return deleted, failed

def main():
    parser = argparse.ArgumentParser(description="Delete all *_merged.json files")
    parser.add_argument("--no-dry-run", action="store_true", 
                       help="Perform actual deletion (default is dry run)")
    args = parser.parse_args()  # args is a Namespace object, NOT a dict
    
    # CORRECT: Access as attribute, not dictionary key
    dry_run = not args.no_dry_run  # Default: dry_run=True; --no-dry-run makes it False
    
    root_dir = Path("assets/data")
    
    if dry_run:
        print("🛡️  DRY RUN MODE (no files will be deleted)\n")
    else:
        print("⚠️  ACTUAL DELETION MODE (files will be permanently removed)\n")
        confirm = input("Type 'YES' to confirm deletion: ").strip()
        if confirm != "YES":
            print("❌ Deletion aborted by user.")
            sys.exit(1)
        print()
    
    merged_files = find_merged_files(root_dir)
    deleted, failed = delete_files(merged_files, dry_run=dry_run)
    
    # Summary
    print("\n" + "="*60)
    print("DELETION SUMMARY")
    print("="*60)
    print(f"Files found:    {len(merged_files)}")
    if not dry_run:
        print(f"Successfully deleted: {deleted}")
        print(f"Failed deletions:     {failed}")
        if failed == 0 and deleted > 0:
            print("\n✅ All *_merged.json files have been removed.")
        elif deleted == 0:
            print("\nℹ️  No files were deleted (none found or all failed).")
    else:
        print("\n💡 This was a DRY RUN. No files were actually deleted.")
        print("   Run with --no-dry-run to perform actual deletion.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation interrupted by user.", file=sys.stderr)
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)