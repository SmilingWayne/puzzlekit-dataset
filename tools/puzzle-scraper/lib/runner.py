from __future__ import annotations

import argparse
import json
import random
import time
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from lib.fetch import fetch_page
from lib.store import (
    allocate_case_id,
    apply_case_id_upgrades,
    grid_rows_cols,
    legacy_zero_case_id,
    load_all_stores,
    merge_legacy_into_fingerprints,
    next_seqs,
    normalize_problem,
    site_ref_from_raw,
    store_cases,
    upgrade_legacy_zero_ids,
)


@dataclass(frozen=True)
class ScraperSpec:
    name: str
    site: str
    file_prefix: str
    default_sizes: list[int]
    output_dir: Path
    description: str


ExtractFn = Callable[[str], dict[str, Any]]
BuildCaseFn = Callable[[dict[str, Any], str, str], dict[str, str]]
CaseIdFn = Callable[[dict[str, Any], int], str | None]
ExpectedDimsFn = Callable[[int], tuple[int, int] | None]


def run_scraper(
    spec: ScraperSpec,
    *,
    sizes: list[int],
    delay_min: float,
    delay_max: float,
    write: bool,
    out_dir: Path,
    summary: Path | None,
    extract: ExtractFn,
    build_case: BuildCaseFn,
    case_id: CaseIdFn,
    expected_dims: ExpectedDimsFn | None = None,
) -> int:
    fetched_at = datetime.now(timezone.utc).isoformat(timespec="seconds")

    if write:
        for old, new in upgrade_legacy_zero_ids(out_dir, spec.file_prefix):
            print(f"UPGRADE {old} -> {new}")

    fingerprints = load_all_stores(out_dir, spec.file_prefix)
    merge_legacy_into_fingerprints(fingerprints, spec.name, out_dir)
    seq_counters = next_seqs(fingerprints["case_id"])

    added: list[tuple[int, str, dict]] = []
    upgrades: list[tuple[str, str, dict]] = []
    skipped: list[tuple[int, str]] = []
    failed: list[tuple[int, str]] = []
    details: dict[str, str] = {}
    t0 = time.monotonic()

    for i, size in enumerate(sizes):
        if i:
            time.sleep(random.uniform(delay_min, delay_max))
        url = f"{spec.site}/?size={size}"
        try:
            raw = extract(fetch_page(spec.site, size))
        except Exception as exc:  # noqa: BLE001 - per-URL robustness
            failed.append((size, str(exc)))
            details[str(size)] = f"FAIL {exc}"
            print(f"size={size:>2}  FAILED  {exc}")
            continue

        if expected_dims is not None:
            expected = expected_dims(size)
            if expected and raw.get("dims") and tuple(raw["dims"]) != expected:
                print(f"size={size:>2}  WARNING dims {raw['dims']} != expected {expected} (site changed?)")

        dims = raw["dims"]
        why = None
        try:
            case = build_case(raw, url, fetched_at)
        except ValueError as exc:
            skipped.append((size, str(exc)))
            details[str(size)] = f"INVALID {exc}"
            print(f"size={size:>2}  INVALID {exc}")
            continue
        site_ref = site_ref_from_raw(raw)
        problem_key = case["problem"]
        problem_norm = normalize_problem(problem_key)
        if site_ref == "N":
            why = "no puzzle id on page"
        elif problem_key in fingerprints["problem"] or problem_norm in fingerprints["problem"]:
            existing_id = fingerprints["problem_to_id"].get(problem_key)
            legacy_cid = case_id(raw, size) if case_id is not None else None
            if (
                existing_id
                and legacy_zero_case_id(existing_id)
                and legacy_cid
                and not legacy_zero_case_id(legacy_cid)
            ):
                upgrades.append((existing_id, legacy_cid, case))
                details[str(size)] = f"UPGRADE {existing_id} -> {legacy_cid}"
                print(f"size={size:>2}  UPGRADE {existing_id} -> {legacy_cid}")
                continue
            why = "duplicate problem"
        if why:
            skipped.append((size, why))
            details[str(size)] = f"SKIP {why}"
            print(f"size={size:>2}  SKIP    {why}")
            continue

        rows, cols = grid_rows_cols(dims)
        cid = allocate_case_id(rows, cols, site_ref, seq_counters)
        added.append((size, cid, case))
        fingerprints["case_id"].add(cid)
        fingerprints["problem"].add(problem_key)
        fingerprints["problem"].add(problem_norm)
        details[str(size)] = f"NEW {cid} {rows}x{cols} {raw.get('ident')}"
        print(f"size={size:>2}  NEW     {cid:<32} {rows}x{cols} {raw.get('ident')}")

    run_secs = round(time.monotonic() - t0, 1)
    print(f"\nadded={len(added)} upgraded={len(upgrades)} skipped={len(skipped)} failed={len(failed)}")

    if write and upgrades:
        for path in apply_case_id_upgrades(upgrades, fingerprints["id_location"]):
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"Upgraded case id(s) in {path} (now {data['count']} cases)")

    if write and added:
        written = store_cases(
            added,
            out_dir,
            name=spec.name,
            file_prefix=spec.file_prefix,
        )
        for path in written:
            data = json.loads(path.read_text(encoding="utf-8"))
            print(f"Stored {data['count']} case(s) -> {path}")
    elif not write:
        print("Dry-run: pass --write to store the new cases.")

    if write and summary is not None:
        total = sum(
            len(json.loads(path.read_text(encoding="utf-8"))["data"])
            for path in sorted(out_dir.glob(f"{spec.file_prefix}_*.json"))
        )
        summary_line = {
            "date": datetime.now().astimezone().strftime("%Y-%m-%d"),
            "utc": fetched_at,
            "added": len(added),
            "skipped": len(skipped),
            "failed": len(failed),
            "total_cases": total,
            "files": [
                {
                    "file": path.name,
                    "count": len(json.loads(path.read_text(encoding="utf-8"))["data"]),
                }
                for path in sorted(out_dir.glob(f"{spec.file_prefix}_*.json"))
            ],
            "details": details,
            "run_secs": run_secs,
        }
        summary.parent.mkdir(parents=True, exist_ok=True)
        with summary.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(summary_line, ensure_ascii=False) + "\n")
        print(f"Summary appended -> {summary}")
    return 0


def build_arg_parser(spec: ScraperSpec) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=spec.description)
    parser.add_argument(
        "--sizes",
        type=int,
        nargs="+",
        default=spec.default_sizes,
        help="size query values to fetch",
    )
    parser.add_argument("--delay-min", type=float, default=4.0, dest="delay_min")
    parser.add_argument("--delay-max", type=float, default=9.0, dest="delay_max")
    parser.add_argument("--write", action="store_true", help="Append scraped cases to the rolling JSON store")
    parser.add_argument(
        "--out",
        type=Path,
        default=spec.output_dir,
        help=f"Store directory (default {spec.output_dir})",
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=None,
        help="Append a JSONL summary line to this file (only with --write)",
    )
    return parser
