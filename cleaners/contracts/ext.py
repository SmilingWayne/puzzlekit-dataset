"""Layout validation and dedupe keys for extended puzzle layouts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from cleaners.contracts.layouts import ValidationResult, _validate_common_lines
from cleaners.contracts.normalization import split_tokens

ExtKind = Literal["boundary", "mathrax"]


@dataclass(frozen=True)
class ExtLayout:
    """Extended problem layout keyed by puzzle-specific shape."""

    kind: ExtKind


def validate_ext_text(text: str, layout: ExtLayout) -> ValidationResult:
    """Validate non-standard line-count layouts using header m n."""

    lines, header, err = _validate_common_lines(text)
    if err:
        return ValidationResult(False, err)
    assert lines is not None and header is not None

    rows, cols = header.rows, header.cols

    if layout.kind == "boundary":
        expected = 1 + (rows + 1)
        if len(lines) != expected:
            return ValidationResult(
                False,
                f"expected {expected} lines (1 + (m+1) boundary rows), got {len(lines)}",
            )
        for row_idx, row in enumerate(lines[1:], start=1):
            token_count = len(split_tokens(row))
            if token_count != cols + 1:
                return ValidationResult(
                    False,
                    f"boundary row {row_idx} has {token_count} cells, expected {cols + 1}",
                )
        return ValidationResult(True, header=header)

    if layout.kind == "mathrax":
        expected = 1 + rows + max(rows - 1, 0)
        if len(lines) != expected:
            return ValidationResult(
                False,
                f"expected {expected} lines (1 + m + (m-1)), got {len(lines)}",
            )

        first_part = lines[1 : 1 + rows]
        second_part = lines[1 + rows :]
        for row_idx, row in enumerate(first_part, start=1):
            token_count = len(split_tokens(row))
            if token_count != cols:
                return ValidationResult(
                    False,
                    f"mathrax clue row {row_idx} has {token_count} cells, expected {cols}",
                )
        for row_idx, row in enumerate(second_part, start=1 + rows):
            token_count = len(split_tokens(row))
            expected_cols = cols - 1
            if token_count != expected_cols:
                return ValidationResult(
                    False,
                    f"mathrax edge row {row_idx} has {token_count} cells, expected {expected_cols}",
                )
        return ValidationResult(True, header=header)

    return ValidationResult(False, f"unsupported ext kind {layout.kind!r}")


def ext_problem_key(problem: str, layout: ExtLayout) -> tuple[object, ...]:
    """Dedupe key for ext layouts; exact match by structured parts."""

    lines = problem.split("\n")
    header = lines[0]

    if layout.kind == "boundary":
        return (header, tuple(lines[1:]))

    if layout.kind == "mathrax":
        rows = int(header.split()[0])
        top_rows = tuple(lines[1 : 1 + rows])
        bottom_rows = tuple(lines[1 + rows :])
        return (header, top_rows, bottom_rows)

    return (problem,)


def make_validate_ext(layout: ExtLayout):
    return lambda text: validate_ext_text(text, layout)


def make_ext_dedupe_key(layout: ExtLayout):
    return lambda problem: ext_problem_key(problem, layout)
