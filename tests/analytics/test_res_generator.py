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


def test_collect_includes_shard_only_puzzle(tmp_path: Path, monkeypatch) -> None:
    from analytics import res_generator as rg
    from cleaners.io import dump_dataset_file, file_payload, shard_path

    monkeypatch.setattr(rg, "ROOT_DIR", tmp_path)
    dump_dataset_file(
        shard_path("Tapa", 0, data_root=tmp_path),
        file_payload(
            "Tapa",
            {
                "8x8_0001_1": {
                    "problem": "2 2\n- -\n- -",
                    "solution": "",
                    "source": "https://example.test/",
                    "info": "",
                }
            },
        ),
    )
    rows, total_problems, total_solutions = rg.collect_table_rows()
    tapa = next(row for row in rows if row[1] == "Tapa")
    assert tapa[2] == "1"
    assert tapa[3] == "0"
    assert total_problems == 1
    assert total_solutions == 0
