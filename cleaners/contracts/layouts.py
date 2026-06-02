"""Layout validation for dataset problem and solution strings."""

from __future__ import annotations

from dataclasses import dataclass

from cleaners.contracts.normalization import _strip_leading_trailing_blank_lines, split_tokens


@dataclass(frozen=True)
class SizeHeader:
    rows: int
    cols: int
    raw_first_line: str


@dataclass(frozen=True)
class ValidationResult:
    valid: bool
    reason: str | None = None
    header: SizeHeader | None = None


def parse_size_header(first_line: str) -> tuple[SizeHeader | None, str | None]:
    parts = first_line.split()
    if len(parts) < 2:
        return None, "header needs at least 'm n'"
    try:
        rows, cols = int(parts[0]), int(parts[1])
    except ValueError:
        return None, "invalid m n in header"
    if rows < 1 or cols < 1:
        return None, "m and n must be positive"
    return SizeHeader(rows=rows, cols=cols, raw_first_line=first_line), None


def _validate_common_lines(text: str) -> tuple[list[str] | None, SizeHeader | None, str | None]:
    lines = text.split("\n") if text else []
    lines = _strip_leading_trailing_blank_lines(lines)
    if not lines:
        return None, None, "empty text"
    if any(line == "" for line in lines):
        return None, None, "blank lines are not allowed"

    header, err = parse_size_header(lines[0])
    if err:
        return None, None, err
    return lines, header, None


def validate_grid_text(text: str) -> ValidationResult:
    """Validate layout 1.1: header plus rows grid lines."""

    lines, header, err = _validate_common_lines(text)
    if err:
        return ValidationResult(False, err)
    assert lines is not None and header is not None

    expected = 1 + header.rows
    if len(lines) != expected:
        return ValidationResult(
            False,
            f"expected {expected} lines (1 + m grid), got {len(lines)}",
        )

    for row_idx, row in enumerate(lines[1:], start=1):
        token_count = len(split_tokens(row))
        if token_count != header.cols:
            return ValidationResult(
                False,
                f"grid row {row_idx} has {token_count} cells, expected {header.cols}",
            )

    return ValidationResult(True, header=header)


def validate_region_text(text: str) -> ValidationResult:
    """Validate layout 1.2: header plus rows clue rows and rows region rows."""

    lines, header, err = _validate_common_lines(text)
    if err:
        return ValidationResult(False, err)
    assert lines is not None and header is not None

    expected = 1 + 2 * header.rows
    if len(lines) != expected:
        return ValidationResult(
            False,
            f"expected {expected} lines (1 + 2m grid), got {len(lines)}",
        )

    for row_idx, row in enumerate(lines[1:], start=1):
        token_count = len(split_tokens(row))
        if token_count != header.cols:
            return ValidationResult(
                False,
                f"row {row_idx} has {token_count} cells, expected {header.cols}",
            )

    return ValidationResult(True, header=header)


def grid_rows(text: str) -> list[str]:
    """Return the grid rows from a valid 1.1 text."""

    return text.split("\n")[1:]


def region_parts(text: str) -> tuple[str, list[str], list[str]]:
    """Return header, clue rows, and region rows from a valid 1.2 text."""

    lines = text.split("\n")
    rows = int(lines[0].split()[0])
    return lines[0], lines[1 : 1 + rows], lines[1 + rows : 1 + 2 * rows]
