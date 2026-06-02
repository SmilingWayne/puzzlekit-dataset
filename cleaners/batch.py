"""Batch dry-run helpers and summary export."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cleaners.contracts import PuzzleCleaningResult
from cleaners.core import clean_dataset_obj
from cleaners.io import DATA_ROOT, load_dataset
from cleaners.registry import get_spec, list_managed_puzzles


def run_batch_dry_run(
    *,
    data_root: Path | None = None,
) -> list[PuzzleCleaningResult]:
    root = data_root or DATA_ROOT
    results: list[PuzzleCleaningResult] = []
    for puzzle_name in list_managed_puzzles():
        source = load_dataset(puzzle_name, data_root=root)
        spec = get_spec(puzzle_name)
        _, result = clean_dataset_obj(source, spec, wrote=False)
        results.append(result)
    return results


def results_to_rows(results: list[PuzzleCleaningResult]) -> list[dict]:
    return [
        {
            "puzzle": r.puzzle,
            "pipeline": r.pipeline,
            "input_total": r.input_total,
            "output_total": r.output_total,
            "modified": r.modified,
            "invalid_removed": r.invalid_removed,
            "duplicate_removed": r.duplicate_removed,
            "count_sol": r.count_sol,
            "error_count": len(r.errors),
            "dedupe_group_count": len(r.dedupe_groups),
            "summary": r.summary_line(),
        }
        for r in results
    ]


def write_batch_summary(
    results: list[PuzzleCleaningResult],
    path: Path,
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    rows = results_to_rows(results)

    total_in = sum(r.input_total for r in results)
    total_out = sum(r.output_total for r in results)
    total_mod = sum(r.modified for r in results)
    total_inv = sum(r.invalid_removed for r in results)
    total_dup = sum(r.duplicate_removed for r in results)

    problems = [r for r in results if r.invalid_removed or r.duplicate_removed or r.modified]
    clean = [r for r in results if r not in problems]

    lines = [
        "# Cleaners batch dry-run summary",
        "",
        f"- **Generated**: {timestamp}",
        f"- **Mode**: dry-run (no JSON writes)",
        f"- **Puzzles**: {len(results)}",
        "",
        "## Totals",
        "",
        f"| Metric | Value |",
        f"|--------|------:|",
        f"| Input cases | {total_in} |",
        f"| Output cases | {total_out} |",
        f"| Modified | {total_mod} |",
        f"| Invalid removed | {total_inv} |",
        f"| Duplicate removed | {total_dup} |",
        "",
        f"- **No changes** (0 modified / 0 removed): {len(clean)} puzzle types",
        f"- **Would change** if written: {len(problems)} puzzle types",
        "",
        "## Per-puzzle",
        "",
        "| Puzzle | Pipeline | In | Out | Modified | Invalid | Dupes |",
        "|--------|----------|---:|----:|---------:|--------:|------:|",
    ]
    for row in sorted(rows, key=lambda item: item["puzzle"]):
        flag = ""
        if row["invalid_removed"] or row["duplicate_removed"] or row["modified"]:
            flag = " ⚠"
        lines.append(
            f"| {row['puzzle']} | {row['pipeline']} | {row['input_total']} | "
            f"{row['output_total']} | {row['modified']} | {row['invalid_removed']} | "
            f"{row['duplicate_removed']} |{flag}"
        )

    if problems:
        lines.extend(["", "## Puzzles with changes", ""])
        for r in sorted(problems, key=lambda x: x.puzzle):
            lines.append(f"### {r.puzzle} (`{r.pipeline}`)")
            lines.append("")
            lines.append(f"- {r.summary_line()}")
            if r.errors[:5]:
                lines.append("- Sample invalid cases:")
                for err in r.errors[:5]:
                    lines.append(f"  - `{err.case_id}`: {err.reason}")
            if r.dedupe_groups[:5]:
                lines.append("- Dedupe groups:")
                for group in r.dedupe_groups[:5]:
                    removed = ", ".join(group.removed_ids)
                    lines.append(f"  - `{group.kept_id}` <- [{removed}]")
            lines.append("")

    md_path = path if path.suffix == ".md" else path.with_suffix(".md")
    json_path = md_path.with_suffix(".json")

    md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    payload = {
        "timestamp_utc": timestamp,
        "mode": "dry-run",
        "totals": {
            "puzzles": len(results),
            "input_total": total_in,
            "output_total": total_out,
            "modified": total_mod,
            "invalid_removed": total_inv,
            "duplicate_removed": total_dup,
            "unchanged_puzzle_count": len(clean),
            "changed_puzzle_count": len(problems),
        },
        "puzzles": rows,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return md_path
