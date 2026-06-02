"""Special layout validation for puzzle-specific pipelines."""

from __future__ import annotations

from cleaners.contracts.layouts import ValidationResult, parse_size_header
from cleaners.contracts.normalization import split_tokens


def validate_nonogram_text(text: str) -> ValidationResult:
    """Validate Nonogram: header + (n column clues) + (m row clues).

    Clue lines may be empty and can have variable token lengths.
    """

    lines = text.split("\n") if text else []
    if not lines:
        return ValidationResult(False, "empty text")

    header, err = parse_size_header(lines[0])
    if err:
        return ValidationResult(False, err)
    assert header is not None

    expected = 1 + header.cols + header.rows
    if len(lines) != expected:
        return ValidationResult(
            False,
            f"expected {expected} lines (1 + n + m), got {len(lines)}",
        )
    return ValidationResult(True, header=header)


def validate_thermometer_text(text: str) -> ValidationResult:
    """Validate Thermometer: header + 2 clue rows + m thermo rows."""

    lines = text.split("\n") if text else []
    if not lines:
        return ValidationResult(False, "empty text")

    header, err = parse_size_header(lines[0])
    if err:
        return ValidationResult(False, err)
    assert header is not None
    rows, cols = header.rows, header.cols

    expected = 1 + 2 + rows
    if len(lines) != expected:
        return ValidationResult(False, f"expected {expected} lines (1 + 2 + m), got {len(lines)}")

    for idx in (1, 2):
        c = len(split_tokens(lines[idx]))
        if c != cols:
            return ValidationResult(False, f"clue row {idx} has {c} cells, expected {cols}")
    for idx, row in enumerate(lines[3:], start=3):
        c = len(split_tokens(row))
        if c != cols:
            return ValidationResult(False, f"thermo row {idx} has {c} cells, expected {cols}")
    return ValidationResult(True, header=header)


def validate_consecutive_text(text: str) -> ValidationResult:
    """Validate ConsecutiveSudoku: header + m sudoku rows + m relation rows."""

    lines = text.split("\n") if text else []
    if not lines:
        return ValidationResult(False, "empty text")

    header, err = parse_size_header(lines[0])
    if err:
        return ValidationResult(False, err)
    assert header is not None
    rows, cols = header.rows, header.cols

    expected = 1 + rows + rows
    if len(lines) != expected:
        return ValidationResult(False, f"expected {expected} lines (1 + m + m), got {len(lines)}")

    for idx, row in enumerate(lines[1:], start=1):
        c = len(split_tokens(row))
        if c != cols:
            return ValidationResult(False, f"row {idx} has {c} cells, expected {cols}")
    return ValidationResult(True, header=header)
