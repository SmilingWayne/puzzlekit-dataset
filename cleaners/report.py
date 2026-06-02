"""Cleaning run reports (JSON + optional changelog markdown)."""

from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from cleaners.contracts import DedupeGroup, PuzzleCleaningResult

REPORTS_DIR = Path(__file__).resolve().parent / "reports"
LATEST_REPORT = REPORTS_DIR / "latest.json"


def _serialize_dedupe_groups(groups: list[DedupeGroup]) -> list[dict]:
    return [
        {"kept_id": group.kept_id, "removed_ids": group.removed_ids}
        for group in groups
    ]


def result_to_dict(result: PuzzleCleaningResult, *, status: str = "ok") -> dict:
    payload = {
        "status": status,
        "puzzle": result.puzzle,
        "pipeline": result.pipeline,
        "wrote": result.wrote,
        "input_total": result.input_total,
        "modified": result.modified,
        "invalid_removed": result.invalid_removed,
        "duplicate_removed": result.duplicate_removed,
        "output_total": result.output_total,
        "count_sol": result.count_sol,
        "summary": result.summary_line(),
        "errors": [asdict(error) for error in result.errors],
        "dedupe_groups": _serialize_dedupe_groups(result.dedupe_groups),
    }
    return payload


def write_report(
    result: PuzzleCleaningResult,
    *,
    status: str = "ok",
    extra: dict | None = None,
) -> Path:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = result_to_dict(result, status=status)
    payload["timestamp_utc"] = timestamp
    if extra:
        payload.update(extra)

    path = REPORTS_DIR / f"{timestamp}_{result.puzzle}.json"
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    with LATEST_REPORT.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    return path


def load_latest_report() -> dict | None:
    if not LATEST_REPORT.is_file():
        return None
    with LATEST_REPORT.open(encoding="utf-8") as handle:
        return json.load(handle)


def _dedup_criterion(pipeline: str) -> str:
    if pipeline == "base":
        return "exact string match on normalized `problem`; keep first in file order"
    if pipeline == "region":
        return (
            "exact header line; exact clue grid when present; region partition "
            "isomorphism on region rows; keep first in file order"
        )
    if pipeline == "rim":
        return (
            "exact header and edge clue rows; body clues exact string or "
            "region partition isomorphism when applicable; keep first in file order"
        )
    return "N/A"


def changelog_markdown(
    result: PuzzleCleaningResult,
    *,
    dataset_path: str,
    rules_applied: list[str] | None = None,
) -> str:
    """Render a RULES.md-compatible section for manual paste into docs/CHANGELOG.md."""

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    rules = rules_applied or [
        f"Pipeline `{result.pipeline}`: normalize problem/solution text",
        "Validate layout; remove invalid cases",
        "Dedupe by pipeline key; keep first case in file order",
    ]
    rules_lines = "\n".join(f"  - {rule}" for rule in rules)
    have_dupes = "Yes" if result.duplicate_removed else "No"
    dedup_criterion = _dedup_criterion(result.pipeline)

    lines = [
        f"## {result.puzzle}",
        "",
        f"- **Timestamp (UTC+0)**: {ts}",
        f"- **Dataset**: `{dataset_path}`",
        "- **Rules applied**:",
        rules_lines,
        f"- **#.Modify**: {result.modified} / {result.input_total}",
        f"- **#.Deduplication**: {result.duplicate_removed}",
        f"- **Dedup criterion**: {dedup_criterion}",
        f"- **Stats: `count`**: {result.output_total}",
        f"- **Stats: `count_sol`**: {result.count_sol}",
        f"- **Have same problem?**: {have_dupes}",
    ]

    if result.invalid_removed:
        lines.append(f"- **Errors**: {result.invalid_removed} invalid case(s) removed")

    if result.duplicate_removed:
        lines.append("- **Duplication (kept → removed)**:")
        for group in result.dedupe_groups[:10]:
            removed = ", ".join(f"`{item}`" for item in group.removed_ids)
            lines.append(f"  - `{group.kept_id}` ← [{removed}]")

    return "\n".join(lines) + "\n"
