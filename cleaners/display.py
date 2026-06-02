"""Human-readable terminal formatting for cleaning results."""

from __future__ import annotations

from cleaners.contracts import PuzzleCleaningResult

_WIDTH = 52
_RULE = "─" * _WIDTH


def _section(title: str, lines: list[str]) -> list[str]:
    out = [title]
    out.extend(f"  {line}" for line in lines)
    return out


def format_result(result: PuzzleCleaningResult, *, status: str = "ok") -> str:
    """Multi-line summary for one puzzle dataset."""

    mode = "write" if result.wrote else "dry-run"
    blocks: list[str] = [
        _RULE,
        f"  {result.puzzle}",
        _RULE,
        *_section(
            "Run",
            [
                f"Status:     {status}",
                f"Pipeline:   {result.pipeline}",
                f"Mode:       {mode}",
            ],
        ),
        "",
        *_section(
            "Cases",
            [
                f"Input:      {result.input_total}",
                f"Output:     {result.output_total}",
                f"Solutions:  {result.count_sol} (non-empty)",
            ],
        ),
        "",
        *_section(
            "Changes",
            [
                f"Modified:   {result.modified}",
                f"Invalid:    {result.invalid_removed} removed",
                f"Duplicate:  {result.duplicate_removed} removed",
            ],
        ),
    ]

    if result.dedupe_groups:
        blocks.append("")
        blocks.append("  Dedupe groups")
        for group in result.dedupe_groups[:5]:
            removed = ", ".join(group.removed_ids)
            blocks.append(f"    kept `{group.kept_id}`  <-  [{removed}]")
        if len(result.dedupe_groups) > 5:
            blocks.append(f"    ... and {len(result.dedupe_groups) - 5} more")

    if result.errors:
        blocks.append("")
        blocks.append("  Invalid samples (first 5)")
        for error in result.errors[:5]:
            blocks.append(f"    `{error.case_id}`: {error.reason}")
        if len(result.errors) > 5:
            blocks.append(f"    ... and {len(result.errors) - 5} more")

    blocks.append(_RULE)
    return "\n".join(blocks)


def format_unchecked(puzzle_name: str) -> str:
    return "\n".join(
        [
            _RULE,
            f"  {puzzle_name}",
            _RULE,
            "  Status:     skipped (not in registry)",
            "  Pipeline:   none",
            _RULE,
        ]
    )


def format_run_banner(*, command: str, puzzles: list[str], write: bool) -> str:
    mode = "write" if write else "dry-run"
    puzzle_list = ", ".join(puzzles) if len(puzzles) <= 5 else f"{len(puzzles)} puzzles"
    return "\n".join(
        [
            "",
            f"cleaners {command}  |  mode: {mode}",
            f"Puzzles: {puzzle_list}",
            "",
        ]
    )


def format_run_totals(results: list[PuzzleCleaningResult]) -> str:
    if len(results) <= 1:
        return ""

    total_in = sum(r.input_total for r in results)
    total_out = sum(r.output_total for r in results)
    total_mod = sum(r.modified for r in results)
    total_inv = sum(r.invalid_removed for r in results)
    total_dup = sum(r.duplicate_removed for r in results)

    return "\n".join(
        [
            _RULE,
            "  Totals (all puzzles above)",
            _RULE,
            f"  Input:      {total_in}",
            f"  Output:     {total_out}",
            f"  Modified:   {total_mod}",
            f"  Invalid:    {total_inv} removed",
            f"  Duplicate:  {total_dup} removed",
            _RULE,
            "",
        ]
    )


def format_report_payload(payload: dict) -> str:
    """Format a JSON report dict for terminal display."""

    from cleaners.contracts import CaseError, DedupeGroup, PuzzleCleaningResult

    errors = [
        CaseError(item["case_id"], item["reason"])
        for item in payload.get("errors", [])
    ]
    dedupe_groups = [
        DedupeGroup(item["kept_id"], item["removed_ids"])
        for item in payload.get("dedupe_groups", [])
    ]
    result = PuzzleCleaningResult(
        puzzle=payload.get("puzzle", "?"),
        pipeline=payload.get("pipeline", "?"),
        input_total=payload.get("input_total", 0),
        modified=payload.get("modified", 0),
        invalid_removed=payload.get("invalid_removed", 0),
        duplicate_removed=payload.get("duplicate_removed", 0),
        output_total=payload.get("output_total", 0),
        count_sol=payload.get("count_sol", 0),
        errors=errors,
        dedupe_groups=dedupe_groups,
        wrote=bool(payload.get("wrote")),
    )
    lines = [format_result(result, status=payload.get("status", "ok"))]
    if ts := payload.get("timestamp_utc"):
        lines.insert(0, f"Report time (UTC): {ts}")
        lines.insert(1, "")
    return "\n".join(lines)
