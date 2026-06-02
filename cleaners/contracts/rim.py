"""Layout validation and dedupe keys for rim (edge-clue) puzzles."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cleaners.contracts.dedupe import canonical_region_rows
from cleaners.contracts.layouts import (
    ValidationResult,
    _validate_common_lines,
    parse_size_header,
)
from cleaners.contracts.normalization import split_tokens

RimBodyKind = Literal["none", "clues", "regions", "clues_regions"]


@dataclass(frozen=True)
class RimLayout:
    """Problem layout: header, edge clue rows, optional body grid."""

    edges: int  # 2 (top+left) or 4 (top+bottom+left+right)
    body: RimBodyKind
    hole_tokens: frozenset[str] = frozenset()
    # When set, also accept header+edges+optional_body rows (e.g. some Skyscraper cases).
    optional_body: RimBodyKind | None = None


def _edge_token_checks(
    lines: list[str],
    *,
    rows: int,
    cols: int,
    edges: int,
) -> str | None:
    if edges == 2:
        if len(split_tokens(lines[1])) != cols:
            return f"top edge row has {len(split_tokens(lines[1]))} tokens, expected {cols}"
        if len(split_tokens(lines[2])) != rows:
            return f"left edge row has {len(split_tokens(lines[2]))} tokens, expected {rows}"
        return None
    if edges == 4:
        for idx in (1, 2):
            count = len(split_tokens(lines[idx]))
            if count != cols:
                return (
                    f"edge row {idx} has {count} tokens, "
                    f"expected {cols} (top/bottom)"
                )
        for idx in (3, 4):
            count = len(split_tokens(lines[idx]))
            if count != rows:
                return (
                    f"edge row {idx} has {count} tokens, "
                    f"expected {rows} (left/right)"
                )
        return None
    return f"unsupported edge count {edges}"


def _expected_line_count(rows: int, edges: int, body: RimBodyKind) -> int:
    base = 1 + edges
    if body == "none":
        return base
    if body == "clues" or body == "regions":
        return base + rows
    return base + 2 * rows


def _resolved_body_kind(layout: RimLayout, line_count: int, rows: int) -> RimBodyKind:
    base = 1 + layout.edges
    if line_count == base:
        return "none"
    if layout.optional_body and line_count == base + rows:
        return layout.optional_body
    return layout.body


def rim_parts(text: str, layout: RimLayout) -> tuple[str, list[str], list[str], list[str]]:
    """Return header, edge lines, clue rows, region rows (empty when absent)."""

    lines = text.split("\n")
    header = lines[0]
    rows = int(header.split()[0])
    edge_end = 1 + layout.edges
    edge_lines = lines[1:edge_end]
    rest = lines[edge_end:]
    body_kind = _resolved_body_kind(layout, len(lines), rows)
    if body_kind == "none":
        return header, edge_lines, [], []
    if body_kind == "clues":
        return header, edge_lines, rest, []
    if body_kind == "regions":
        return header, edge_lines, [], rest
    clue_rows = rest[:rows]
    region_rows = rest[rows : 2 * rows]
    return header, edge_lines, clue_rows, region_rows


def validate_rim_text(text: str, layout: RimLayout) -> ValidationResult:
    """Validate rim layout: header, edge rows, optional body."""

    lines, header, err = _validate_common_lines(text)
    if err:
        return ValidationResult(False, err)
    assert lines is not None and header is not None

    rows, cols = header.rows, header.cols
    if layout.edges not in (2, 4):
        return ValidationResult(False, f"unsupported edges={layout.edges}")

    expected = _expected_line_count(rows, layout.edges, layout.body)
    allowed = {expected}
    if layout.optional_body:
        allowed.add(_expected_line_count(rows, layout.edges, layout.optional_body))
    if len(lines) not in allowed:
        allowed_str = ", ".join(str(value) for value in sorted(allowed))
        return ValidationResult(
            False,
            f"expected {allowed_str} lines for rim({layout.edges},{layout.body}), "
            f"got {len(lines)}",
        )
    body_kind = _resolved_body_kind(layout, len(lines), rows)

    edge_err = _edge_token_checks(lines, rows=rows, cols=cols, edges=layout.edges)
    if edge_err:
        return ValidationResult(False, edge_err)

    body_start = 1 + layout.edges
    if body_kind == "none":
        return ValidationResult(True, header=header)

    if body_kind in ("clues", "regions"):
        for row_idx, row in enumerate(lines[body_start:], start=body_start):
            token_count = len(split_tokens(row))
            if token_count != cols:
                return ValidationResult(
                    False,
                    f"body row {row_idx} has {token_count} cells, expected {cols}",
                )
        return ValidationResult(True, header=header)

    for row_idx, row in enumerate(lines[body_start:], start=body_start):
        token_count = len(split_tokens(row))
        if token_count != cols:
            return ValidationResult(
                False,
                f"body row {row_idx} has {token_count} cells, expected {cols}",
            )
    return ValidationResult(True, header=header)


def rim_problem_key(problem: str, layout: RimLayout) -> tuple[object, ...]:
    """Dedupe: exact header + exact edge lines + body per kind."""

    lines = problem.split("\n")
    rows = int(lines[0].split()[0])
    body_kind = _resolved_body_kind(layout, len(lines), rows)
    header, edge_lines, clue_rows, region_rows = rim_parts(problem, layout)
    edge_key: tuple[str, ...] = tuple(edge_lines)

    if body_kind == "none":
        return (header, edge_key)

    if body_kind == "clues":
        return (header, edge_key, "\n".join(clue_rows))

    if body_kind == "regions":
        return (
            header,
            edge_key,
            canonical_region_rows(region_rows, hole_tokens=layout.hole_tokens),
        )

    return (
        header,
        edge_key,
        "\n".join(clue_rows),
        canonical_region_rows(region_rows, hole_tokens=layout.hole_tokens),
    )


def make_validate_rim(layout: RimLayout):
    return lambda text: validate_rim_text(text, layout)


def make_rim_dedupe_key(layout: RimLayout):
    return lambda problem: rim_problem_key(problem, layout)
