"""CLI for puzz.link catalog ingest and dataset promotion."""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

from cleaners.io import DATA_ROOT
from ingest.promote import materialize_ref, promote, refresh_readme_stats

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CATALOG = REPO_ROOT / "puzzlink_crawlers" / "logs" / "merged_puzzles.csv"
TYPE_MAP_PATH = REPO_ROOT / "ingest" / "type_map.yaml"
REPORT_DIR = REPO_ROOT / "ingest" / "reports"


def _save_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_type_map() -> dict:
    import yaml

    with TYPE_MAP_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def run_ingest(args: argparse.Namespace) -> int:
    import copy

    from cleaners.io import load_dataset, save_dataset
    from ingest.catalog import load_catalog
    from ingest.merge import merge_results
    from ingest.pipeline import IngestResult, build_dedupe_index, process_entry

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

    dataset = load_dataset(dataset_name)
    original_data = copy.deepcopy(dataset.get("data", {}))
    existing_urls, existing_problems = build_dedupe_index(dataset)

    results = []
    for idx, entry in enumerate(entries, start=1):
        if entry.puzz_link_url in existing_urls:
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
    _save_report(report, report_path)

    print(json.dumps(report, indent=2))
    print(f"Report written to {report_path}")

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


def build_catalog_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ingest",
        description="Ingest puzz.link catalog entries into dataset JSON.",
    )
    parser.add_argument("puzzle", help="Puzzle key in ingest/type_map.yaml (e.g. masyu)")
    parser.add_argument("--catalog", default=str(DEFAULT_CATALOG), help="Path to merged_puzzles.csv")
    parser.add_argument(
        "--limit",
        type=int,
        default=200,
        help="Process at most N catalog entries (0 = all; default 200 pilot)",
    )
    parser.add_argument(
        "--time-limit",
        type=float,
        default=60.0,
        dest="time_limit",
        help="Solver time limit (seconds)",
    )
    parser.add_argument("--write", action="store_true", help="Write merged dataset to assets/")
    return parser


def build_promote_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m ingest promote",
        description=(
            "Promote already-formed dataset JSON into canonical shards. "
            "Append-only: never rewrite earlier shards; empty solutions are kept."
        )
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "--source",
        type=Path,
        help="Repo root, assets/data, a puzzle directory, or a single dataset JSON file",
    )
    source.add_argument(
        "--from-ref",
        dest="from_ref",
        help="Git ref whose assets/data to promote (e.g. origin/ingest/daily)",
    )
    parser.add_argument(
        "--puzzle",
        action="append",
        dest="puzzles",
        metavar="NAME",
        help="Limit to these puzzle names (repeatable)",
    )
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Destination assets/data root (default: repo assets/data)",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write new cases onto destination shards (default: dry-run)",
    )
    parser.add_argument(
        "--stats",
        action="store_true",
        help="After --write, refresh the README stats table",
    )
    return parser


def _printable_promote_report(batch: dict, *, id_limit: int = 20) -> dict:
    """Copy a promote report, truncating added_ids for stdout."""
    printable = json.loads(json.dumps(batch))
    for item in printable.get("puzzles") or []:
        ids = item.get("added_ids") or []
        if len(ids) > id_limit:
            item["added_ids"] = ids[:id_limit]
            item["added_ids_omitted"] = len(ids) - id_limit
    return printable


def run_promote(args: argparse.Namespace) -> int:
    tmp_root: Path | None = None
    try:
        if args.from_ref:
            try:
                tmp_root = materialize_ref(args.from_ref)
            except RuntimeError as exc:
                print(f"Failed to read git ref {args.from_ref!r}: {exc}", file=sys.stderr)
                return 2
            source = tmp_root
            source_label = args.from_ref
        else:
            source = Path(args.source)
            if not source.exists():
                print(f"Source not found: {source}", file=sys.stderr)
                return 2
            source_label = str(source)

        only = set(args.puzzles) if args.puzzles else None
        _reports, batch = promote(
            source=source,
            dest_root=Path(args.data_root),
            only=only,
            write=args.write,
            source_label=source_label,
        )
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        report_path = REPORT_DIR / f"promote_{stamp}.json"
        _save_report(batch, report_path)
        print(json.dumps(_printable_promote_report(batch), indent=2, ensure_ascii=False))
        print(f"Report written to {report_path}")
        if not args.write:
            print("Dry-run only (pass --write to append onto destination shards).")
        elif args.stats:
            refresh_readme_stats()
        return 0
    finally:
        if tmp_root is not None:
            shutil.rmtree(tmp_root, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] == "promote":
        return run_promote(build_promote_parser().parse_args(args[1:]))
    if args and args[0] == "catalog":
        return run_ingest(build_catalog_parser().parse_args(args[1:]))
    return run_ingest(build_catalog_parser().parse_args(args))


if __name__ == "__main__":
    raise SystemExit(main())
