"""Merge ingested cases into a dataset JSON object."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from ingest.pipeline import IngestResult, _normalize_problem_key


def recount(dataset: dict) -> None:
    data = dataset.get("data", {})
    dataset["count"] = len(data)
    dataset["count_sol"] = sum(1 for case in data.values() if str(case.get("solution", "")).strip())


def merge_results(
    dataset: dict,
    results: list[IngestResult],
    *,
    existing_urls: set[str],
    existing_problems: set[str],
) -> dict[str, Any]:
    """Append new cases; return a report dict."""
    merged = copy.deepcopy(dataset)
    data: dict[str, Any] = merged.setdefault("data", {})

    report = {
        "added": 0,
        "skipped_url_dup": 0,
        "skipped_problem_dup": 0,
        "failed": 0,
        "failures": [],
        "added_ids": [],
    }

    used_ids = set(data.keys())

    for result in results:
        if not result.ok:
            if result.skip_reason:
                key = "skipped_url_dup" if "url" in result.skip_reason else "skipped_problem_dup"
                report[key] += 1
            else:
                report["failed"] += 1
                if len(report["failures"]) < 50:
                    report["failures"].append(
                        {"name": result.entry.name, "url": result.entry.puzz_link_url, "error": result.error}
                    )
            continue

        assert result.case is not None
        url = result.entry.puzz_link_url
        if url in existing_urls:
            report["skipped_url_dup"] += 1
            continue

        problem_key = _normalize_problem_key(result.case["problem"])
        if problem_key in existing_problems:
            report["skipped_problem_dup"] += 1
            continue

        case_id = result.case_id
        base_id = case_id
        suffix = 1
        while case_id in used_ids:
            case_id = f"{base_id}_{suffix}"
            suffix += 1

        data[case_id] = result.case
        used_ids.add(case_id)
        existing_urls.add(url)
        existing_problems.add(problem_key)
        report["added"] += 1
        report["added_ids"].append(case_id)

    recount(merged)
    return {"dataset": merged, "report": report}


def save_report(report: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
