"""Text normalization helpers for puzzle dataset strings."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class NormalizeResult:
    text: str
    changed: bool


def split_tokens(line: str) -> list[str]:
    """Split a grid row into non-empty tokens."""

    return line.strip().split()


def _strip_leading_trailing_blank_lines(lines: list[str]) -> list[str]:
    """Remove empty lines only at the start and end of the sequence."""

    start = 0
    end = len(lines)
    while start < end and lines[start] == "":
        start += 1
    while end > start and lines[end - 1] == "":
        end -= 1
    return lines[start:end]


def normalize_grid_text(text: str) -> NormalizeResult:
    """Normalize line boundaries and token spacing.

    Each line is stripped, and non-empty lines are collapsed to single-space
    token separators. Leading and trailing empty lines are dropped (common
    from a final ``\\n`` in JSON strings). Empty lines in the middle are kept
    so validation can still reject them.
    """

    if not isinstance(text, str):
        text = str(text)

    normalized_newlines = text.replace("\r\n", "\n").replace("\r", "\n")
    out: list[str] = []
    for line in normalized_newlines.split("\n"):
        stripped = line.strip()
        out.append(" ".join(stripped.split()) if stripped else "")

    out = _strip_leading_trailing_blank_lines(out)
    normalized = "\n".join(out)
    return NormalizeResult(normalized, normalized != text)
