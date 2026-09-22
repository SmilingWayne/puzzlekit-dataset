#!/usr/bin/env python3
"""Pack leftover monolith + daily shards into one 000-based sequence.

Intended for ingest/daily dual-track folders (Masyu, Shingoki, Hashi,
Shakashaka, LITS). Tapa is skipped unless it still has a monolith.
Pause scheduled scrape before --write.
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
    cases_legacy_then_shards,
    dataset_path,
    load_dataset,
    repack_to_shards,
    shard_paths,
)

DAILY_DUAL = ("Masyu", "Shingoki", "Hashi", "Shakashaka", "LITS", "Tapa")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--data-root", type=Path, default=DATA_ROOT)
    parser.add_argument("--puzzle", action="append", dest="puzzles")
    args = parser.parse_args(argv)

    names = tuple(args.puzzles) if args.puzzles else DAILY_DUAL
    for name in names:
        legacy = dataset_path(name, data_root=args.data_root)
        shards = shard_paths(name, data_root=args.data_root)
        if not legacy.is_file() and not shards:
            print(f"{name}: missing")
            continue
        if not legacy.is_file():
            print(f"{name}: shards only ({len(shards)} files), skip")
            continue
        name_label, cases = cases_legacy_then_shards(name, data_root=args.data_root)
        n = len(cases)
        need = max(1, (n + 499) // 500)
        print(
            f"{name}: union={n} legacy={legacy.is_file()} "
            f"old_shards={len(shards)} -> {need} shards"
        )
        if not args.write:
            continue
        before_ids = list(cases)
        written = repack_to_shards(
            name,
            cases,
            name=name_label,
            data_root=args.data_root,
        )
        after = load_dataset(name, data_root=args.data_root)
        if list(after["data"]) != before_ids:
            print(f"ERROR {name}: id order changed after pack", file=sys.stderr)
            return 1
        print(f"  wrote {[path.name for path in written]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
