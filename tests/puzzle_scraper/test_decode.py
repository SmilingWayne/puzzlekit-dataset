from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "puzzle-scraper"))

from lib.store import build_problem
from sites.hashi import decode_task as decode_hashi
from sites.masyu import decode_task as decode_masyu
from sites.shakashaka import decode_task as decode_shakashaka
from sites.shingoki import decode_task as decode_shingoki, grid_dims


def test_shingoki_live_style_task() -> None:
    task = "eB3W2bB3gB2bB2fB5B2aB6e"
    cells = decode_shingoki(task)
    grid = grid_dims((5, 5))
    assert len(cells) == grid[0] * grid[1]
    assert cells[5] == "b3"


def test_masyu_decode() -> None:
    cells = decode_masyu("WaB")
    assert cells == ["w", "-", "b"]


def test_shakashaka_user_example() -> None:
    task = "i1aBe2g"
    cells = decode_shakashaka(task)
    assert len(cells) == 25
    w = 5
    assert cells[1 * w + 4] == "1"
    assert cells[2 * w + 1] == "x"
    assert cells[3 * w + 2] == "2"


def test_shakashaka_live_style_task() -> None:
    task = "e2g1Be1d"
    cells = decode_shakashaka(task)
    assert len(cells) == 25
    w = 5
    assert cells[1 * w + 0] == "2"
    assert cells[2 * w + 3] == "1"
    assert cells[2 * w + 4] == "x"
    assert cells[4 * w + 0] == "1"


def test_shakashaka_build_problem() -> None:
    cells = decode_shakashaka("i1aBe2g")
    problem = build_problem((5, 5), cells)
    lines = problem.splitlines()
    assert lines[0] == "5 5"
    assert len(lines) == 6


def test_shakashaka_invalid_char() -> None:
    try:
        decode_shakashaka("i1aXe2g")
    except ValueError as exc:
        assert "unexpected character" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_hashi_user_7x7() -> None:
    cells = decode_hashi("4a3c2a4c3h3a3b3d1b31a1e3d2")
    assert len(cells) == 49
    w = 7
    assert cells[3 * w + 0] == "3"
    assert cells[3 * w + 2] == "3"
    assert all(cell == "-" for cell in cells[2 * w : 3 * w])
    assert cells[1 * w + 5] == "3"
    assert cells[6 * w + 6] == "2"
    assert sum(cell.isdigit() for cell in cells) == 14
    problem = build_problem((7, 7), cells)
    assert problem.splitlines() == [
        "7 7",
        "4 - 3 - - - 2",
        "- 4 - - - 3 -",
        "- - - - - - -",
        "3 - 3 - - 3 -",
        "- - - 1 - - 3",
        "1 - 1 - - - -",
        "- 3 - - - - 2",
    ]


def test_hashi_user_10x10() -> None:
    cells = decode_hashi("a2a4d3j1a2b4c4a2j1b3a3a3a6b6e3k1a5b4b4j3h2")
    assert len(cells) == 100
    w = 10
    assert cells[9 * w + 9] == "2"
    assert cells[7 * w + 6] == "4"


def test_hashi_invalid_char() -> None:
    try:
        decode_hashi("4aX3")
    except ValueError as exc:
        assert "unexpected character" in str(exc)
    else:
        raise AssertionError("expected ValueError")


if __name__ == "__main__":
    test_shingoki_live_style_task()
    test_masyu_decode()
    test_shakashaka_user_example()
    test_shakashaka_live_style_task()
    test_shakashaka_build_problem()
    test_shakashaka_invalid_char()
    test_hashi_user_7x7()
    test_hashi_user_10x10()
    test_hashi_invalid_char()
    print("ok")
