"""Unified region pipeline: partition dedupe with optional clue grid (1+m or 1+2m)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cleaners.contracts.dedupe import RegionKey, canonical_region_rows
from cleaners.contracts.layouts import (
    ValidationResult,
    _validate_common_lines,
    region_parts,
)
from cleaners.contracts.normalization import split_tokens

RegionBodyKind = Literal["regions", "clues_regions"]

DEFAULT_REGION_HOLE_TOKENS = frozenset({"@"})
REGION_PARTITION_HOLE_TOKENS = frozenset({"@", "#"})


@dataclass(frozen=True)
class RegionLayout:
    """Per-puzzle region cleaning layout (no line-count inference)."""

    body: RegionBodyKind
    hole_tokens: frozenset[str] = DEFAULT_REGION_HOLE_TOKENS


def _expected_line_count(rows: int, body: RegionBodyKind) -> int:
    if body == "regions":
        return 1 + rows
    return 1 + 2 * rows


def region_layout_parts(
    text: str,
    layout: RegionLayout,
) -> tuple[str, list[str], list[str]]:
    """Return header, clue rows (maybe empty), region rows."""

    lines = text.split("\n")
    header = lines[0]
    rows = int(header.split()[0])
    if layout.body == "regions":
        return header, [], lines[1 : 1 + rows]
    _header, clue_rows, region_rows = region_parts(text)
    return header, clue_rows, region_rows


def validate_region_layout_text(text: str, layout: RegionLayout) -> ValidationResult:
    """Validate 1+m (regions only) or 1+2m (clues + regions)."""

    lines, header, err = _validate_common_lines(text)
    if err:
        return ValidationResult(False, err)
    assert lines is not None and header is not None

    rows, cols = header.rows, header.cols
    expected = _expected_line_count(rows, layout.body)
    if len(lines) != expected:
        return ValidationResult(
            False,
            f"expected {expected} lines for region({layout.body}), got {len(lines)}",
        )

    for row_idx, row in enumerate(lines[1:], start=1):
        token_count = len(split_tokens(row))
        if token_count != cols:
            return ValidationResult(
                False,
                f"row {row_idx} has {token_count} cells, expected {cols}",
            )

    return ValidationResult(True, header=header)


def region_layout_problem_key(problem: str, layout: RegionLayout) -> tuple[object, ...]:
    """Dedupe: exact header; clues exact when present; regions canonical."""

    header, clue_rows, region_rows = region_layout_parts(problem, layout)
    region_key: RegionKey = canonical_region_rows(
        region_rows,
        hole_tokens=layout.hole_tokens,
    )
    if layout.body == "regions":
        return (header, region_key)
    return (header, "\n".join(clue_rows), region_key)


def make_validate_region(layout: RegionLayout):
    return lambda text: validate_region_layout_text(text, layout)


def make_region_dedupe_key(layout: RegionLayout):
    return lambda problem: region_layout_problem_key(problem, layout)
