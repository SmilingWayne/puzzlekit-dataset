"""CLI for puzz.link ingest."""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from cleaners.io import dataset_path, save_dataset
from ingest.catalog import load_catalog
from ingest.merge import merge_results, save_report
from ingest.pipeline import build_dedupe_index, process_entry

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "puzzlink_crawlers" / "logs" / "merged_puzzles.csv"
TYPE_MAP_PATH = REPO_ROOT / "ingest" / "type_map.yaml"
REPORT_DIR = REPO_ROOT / "ingest" / "reports"


def _load_type_map() -> dict:
    with TYPE_MAP_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _load_dataset(puzzle_name: str) -> dict:
    path = dataset_path(puzzle_name)
    return json.loads(path.read_text(encoding="utf-8"))


def run_ingest(args: argparse.Namespace) -> int:
    type_map = _load_type_map()
    spec = type_map.get(args.puzzle)
    if spec is None:
        print(f"Unknown puzzle key {args.puzzle!r} in type_map.yaml", file=sys.stderr)
        return 2

    dataset_name = spec["dataset_name"]
    puzzlekit_type = spec["puzzlekit_type"]
    catalog_types = set(spec.get("catalog_types", [args.puzzle]))

    catalog_path = Path(args.catalog)
    entries = load_catalog(catalog_path, catalog_types=catalog_types)
    if args.limit and args.limit > 0:
        entries = entries[: args.limit]

    print(f"Catalog entries for {args.puzzle}: {len(entries)}")

    dataset = _load_dataset(dataset_name)
    original_data = copy.deepcopy(dataset.get("data", {}))
    existing_urls, existing_problems = build_dedupe_index(dataset)

    results = []
    for idx, entry in enumerate(entries, start=1):
        if entry.puzz_link_url in existing_urls:
            from ingest.pipeline import IngestResult

            results.append(
                IngestResult(entry=entry, ok=False, skip_reason="url_dup_precheck")
            )
            continue
        if idx % 25 == 0 or idx == 1:
            print(f"  processing {idx}/{len(entries)} …")
        results.append(
            process_entry(entry, puzzlekit_type=puzzlekit_type, time_limit_sec=args.time_limit)
        )

    merged = merge_results(
        dataset,
        results,
        existing_urls=existing_urls,
        existing_problems=existing_problems,
    )
    out_dataset = merged["dataset"]
    report = merged["report"]
    report["puzzle"] = args.puzzle
    report["dataset_name"] = dataset_name
    report["catalog_entries"] = len(entries)
    report["timestamp"] = datetime.now(timezone.utc).isoformat()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"{args.puzzle}_{stamp}.json"
    save_report(report, report_path)

    print(json.dumps(report, indent=2))
    print(f"Report written to {report_path}")

    # Verify original cases unchanged
    for case_id, case in original_data.items():
        if out_dataset["data"].get(case_id) != case:
            print(f"ERROR: existing case modified: {case_id}", file=sys.stderr)
            return 1

    if args.write:
        out_path = save_dataset(dataset_name, out_dataset, backup=True)
        print(f"Wrote {out_path}")
    else:
        print("Dry-run only (pass --write to update assets).")

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Ingest puzz.link catalog entries into dataset JSON.")
    parser.add_argument("puzzle", help="Puzzle key in ingest/type_map.yaml (e.g. masyu)")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Path to merged_puzzles.csv")
    parser.add_argument("--limit", type=int, default=200, help="Process at most N catalog entries (0 = all; default 200 pilot)")
    parser.add_argument("--time-limit", type=float, default=60.0, dest="time_limit", help="Solver time limit (seconds)")
    parser.add_argument("--write", action="store_true", help="Write merged dataset to assets/")
    return parser


def main(argv: list[str] | None = None) -> int:
    return run_ingest(build_parser().parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
