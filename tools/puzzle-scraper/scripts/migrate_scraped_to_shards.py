#!/usr/bin/env python3
"""One-shot: move assets/scraped into assets/data/{Puzzle}/{Puzzle}_dataset_yyy.json."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[1]
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from lib.store import (
    allocate_case_id,
    legacy_problems,
    normalize_problem,
    shard_prefix,
    site_ref_from_old_id,
    store_cases,
)

REPO_ROOT = TOOLS_DIR.parent.parent
SCRAPED_ROOT = REPO_ROOT / "assets" / "scraped"
DATA_ROOT = REPO_ROOT / "assets" / "data"

PUZZLES: tuple[tuple[str, str], ...] = (
    ("masyu", "Masyu"),
    ("shingoki", "Shingoki"),
    ("shakashaka", "Shakashaka"),
    ("hashi", "Hashi"),
    ("tapa", "Tapa"),
    ("lits", "LITS"),
)


def rows_cols_from_problem(problem: str) -> tuple[int, int]:
    header = problem.splitlines()[0]
    parts = header.split()
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        raise ValueError(f"bad problem header: {header!r}")
    return int(parts[0]), int(parts[1])


def load_scraped_cases(kind: str) -> list[tuple[str, dict]]:
    directory = SCRAPED_ROOT / kind
    cases: list[tuple[str, dict]] = []
    if not directory.is_dir():
        return cases
    for path in sorted(directory.glob(f"{kind}_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        for cid, case in data.get("data", {}).items():
            cases.append((cid, case))
    cases.sort(key=lambda item: (str(item[1].get("fetched_at") or ""), item[0]))
    return cases


def migrate_one(kind: str, puzzle_name: str) -> dict:
    out_dir = DATA_ROOT / puzzle_name
    prefix = shard_prefix(puzzle_name)
    skip = legacy_problems(out_dir / f"{puzzle_name}_dataset.json")
    counters: dict[tuple[int, int], int] = {}
    added: list[tuple[int, str, dict]] = []
    skipped_legacy = 0
    skipped_dup = 0
    seen_problems: set[str] = set(skip)

    for old_id, case in load_scraped_cases(kind):
        problem = case.get("problem") or ""
        keys = {problem, normalize_problem(problem)}
        if keys & seen_problems:
            if keys & skip:
                skipped_legacy += 1
            else:
                skipped_dup += 1
            continue
        rows, cols = rows_cols_from_problem(problem)
        site_ref = site_ref_from_old_id(old_id)
        cid = allocate_case_id(rows, cols, site_ref, counters)
        added.append((0, cid, case))
        seen_problems.update(keys)

    written: list[Path] = []
    if added:
        written = store_cases(added, out_dir, name=puzzle_name, file_prefix=prefix)

    scraped_dir = SCRAPED_ROOT / kind
    if scraped_dir.is_dir():
        shutil.rmtree(scraped_dir)

    return {
        "puzzle": puzzle_name,
        "migrated": len(added),
        "skipped_legacy": skipped_legacy,
        "skipped_dup": skipped_dup,
        "files": [path.name for path in written],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)
    if args.dry_run:
        for kind, name in PUZZLES:
            cases = load_scraped_cases(kind)
            skip = legacy_problems(DATA_ROOT / name / f"{name}_dataset.json")
            keep = 0
            skipped = 0
            seen: set[str] = set(skip)
            for _cid, case in cases:
                problem = case.get("problem") or ""
                keys = {problem, normalize_problem(problem)}
                if keys & seen:
                    skipped += 1
                    continue
                keep += 1
                seen.update(keys)
            print(f"{name}: scraped={len(cases)} migrate={keep} skip={skipped}")
        return 0

    reports = [migrate_one(kind, name) for kind, name in PUZZLES]
    for report in reports:
        print(
            f"{report['puzzle']}: migrated={report['migrated']} "
            f"skipped_legacy={report['skipped_legacy']} skipped_dup={report['skipped_dup']} "
            f"files={report['files']}"
        )
    if SCRAPED_ROOT.is_dir() and not any(SCRAPED_ROOT.iterdir()):
        SCRAPED_ROOT.rmdir()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
