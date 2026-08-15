from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools" / "puzzle-scraper"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from lib.store import MAX_PER_FILE, load_all_stores, store_cases


def _case(cid: str) -> dict:
    return {
        "problem": f"2 2\n- -\n- {cid}",
        "solution": "",
        "source": "https://example.test/",
        "info": "test",
        "fetched_at": "2026-08-15T00:00:00+00:00",
    }


def test_store_rolls_to_new_file(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("lib.store.MAX_PER_FILE", 2)
    added = [
        (0, "size0_a", _case("a")),
        (0, "size0_b", _case("b")),
        (0, "size0_c", _case("c")),
    ]
    written = store_cases(added, tmp_path, name="Masyu", file_prefix="masyu")
    assert [path.name for path in written] == ["masyu_001.json", "masyu_002.json"]
    first = json.loads((tmp_path / "masyu_001.json").read_text(encoding="utf-8"))
    second = json.loads((tmp_path / "masyu_002.json").read_text(encoding="utf-8"))
    assert first["count"] == 2
    assert second["count"] == 1
    assert set(first["data"]) == {"size0_a", "size0_b"}
    assert set(second["data"]) == {"size0_c"}


def test_load_all_stores_fingerprints(tmp_path) -> None:
    store_cases([(0, "size0_a", _case("a"))], tmp_path, name="Masyu", file_prefix="masyu")
    fingerprints = load_all_stores(tmp_path, "masyu")
    assert "size0_a" in fingerprints["case_id"]
    assert _case("a")["problem"] in fingerprints["problem"]


def test_default_cap_is_500() -> None:
    assert MAX_PER_FILE == 500
