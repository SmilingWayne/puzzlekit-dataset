"""Tests for README stats injection."""

from pathlib import Path

import pytest

from analytics.res_generator import INJECT_MARKER, build_markdown_table, inject_readme


def test_inject_replaces_between_markers(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text(
        "# Title\n\n"
        f"{INJECT_MARKER}\n"
        "| old | table |\n"
        f"{INJECT_MARKER}\n\n"
        "## After\n",
        encoding="utf-8",
    )

    inject_readme(readme)

    text = readme.read_text(encoding="utf-8")
    assert "| old | table |" not in text
    assert "## After" in text
    assert text.count(INJECT_MARKER) == 2
    assert "| No. | Puzzle Name |" in text


def test_inject_missing_marker_raises(tmp_path: Path) -> None:
    readme = tmp_path / "README.md"
    readme.write_text("# no markers\n", encoding="utf-8")
    with pytest.raises(ValueError, match="Opening marker"):
        inject_readme(readme)


def test_build_markdown_table_has_total_row() -> None:
    table = build_markdown_table()
    assert "**Total**" in table
    assert "| --- |" in table
