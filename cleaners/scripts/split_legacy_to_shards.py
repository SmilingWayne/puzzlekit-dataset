#!/usr/bin/env python3
"""Split leftover *_dataset.json monoliths into 500-case shards.

Skips daily dual-track puzzles (legacy + ingest shards in the same folder).
Default is dry-run. Pass --write to rewrite files.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from cleaners.io import (
    DATA_ROOT,
    dataset_path,
    list_puzzle_dirs,
    load_dataset,
    shard_paths,
    split_monolith_to_shards,
)

DAILY_DUAL = frozenset({"Masyu", "Shingoki", "Hashi", "Shakashaka", "LITS", "Tapa"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    args = parser.parse_args(argv)

    split: list[str] = []
    skipped_dual: list[str] = []
    skipped_existing: list[str] = []
    skipped_none: list[str] = []

    for name in list_puzzle_dirs(data_root=args.data_root):
        legacy = dataset_path(name, data_root=args.data_root)
        shards = shard_paths(name, data_root=args.data_root)
        if name in DAILY_DUAL:
            skipped_dual.append(name)
            continue
        if not legacy.is_file():
            skipped_none.append(name)
            continue
        if shards:
            skipped_existing.append(name)
            continue
        before = load_dataset(name, data_root=args.data_root)
        n = before["count"]
        if args.write:
            written = split_monolith_to_shards(name, data_root=args.data_root)
            after = load_dataset(name, data_root=args.data_root)
            if after["count"] != n or list(after["data"]) != list(before["data"]):
                print(f"ERROR {name}: count/id mismatch after split", file=sys.stderr)
                return 1
            print(f"{name}: {n} cases -> {len(written)} shards")
        else:
            shards_needed = max(1, (n + 499) // 500) if n else 1
            print(f"{name}: {n} cases -> {shards_needed} shards (dry-run)")
        split.append(name)

    print(
        f"split={len(split)} skipped_dual={len(skipped_dual)} "
        f"skipped_has_shards={len(skipped_existing)} skipped_no_legacy={len(skipped_none)} "
        f"write={args.write}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
