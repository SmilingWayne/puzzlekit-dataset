from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools" / "puzzle-scraper"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from lib.store import (
    MAX_PER_FILE,
    format_case_id,
    legacy_problems,
    load_all_stores,
    next_seqs,
    parse_case_id,
    shard_prefix,
    site_ref_from_old_id,
    site_ref_from_raw,
    store_cases,
)


def _case(cid: str) -> dict:
    return {
        "problem": f"2 2\n- -\n- {cid}",
        "solution": "",
        "source": "https://example.test/",
        "info": "test",
        "fetched_at": "2026-08-15T00:00:00+00:00",
    }


def test_store_rolls_to_new_file_zero_indexed(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr("lib.store.MAX_PER_FILE", 2)
    added = [
        (0, "2x2_0001_a", _case("a")),
        (0, "2x2_0002_b", _case("b")),
        (0, "2x2_0003_c", _case("c")),
    ]
    written = store_cases(added, tmp_path, name="Masyu", file_prefix="Masyu_dataset")
    assert [path.name for path in written] == ["Masyu_dataset_000.json", "Masyu_dataset_001.json"]
    first = json.loads((tmp_path / "Masyu_dataset_000.json").read_text(encoding="utf-8"))
    second = json.loads((tmp_path / "Masyu_dataset_001.json").read_text(encoding="utf-8"))
    assert first["count"] == 2
    assert second["count"] == 1
    assert set(first["data"]) == {"2x2_0001_a", "2x2_0002_b"}
    assert set(second["data"]) == {"2x2_0003_c"}


def test_load_all_stores_fingerprints(tmp_path) -> None:
    store_cases([(0, "2x2_0001_a", _case("a"))], tmp_path, name="Masyu", file_prefix="Masyu_dataset")
    fingerprints = load_all_stores(tmp_path, "Masyu_dataset")
    assert "2x2_0001_a" in fingerprints["case_id"]
    assert _case("a")["problem"] in fingerprints["problem"]


def test_load_all_stores_ignores_legacy_dataset_json(tmp_path) -> None:
    legacy = {
        "name": "Masyu",
        "count": 1,
        "count_sol": 1,
        "data": {
            "02_2x2": {
                "problem": "2 2\nw -\n- b",
                "solution": "se sw\nne nw",
                "source": "https://janko.at/",
            }
        },
    }
    (tmp_path / "Masyu_dataset.json").write_text(json.dumps(legacy), encoding="utf-8")
    store_cases([(0, "2x2_0001_9", _case("a"))], tmp_path, name="Masyu", file_prefix="Masyu_dataset")
    fingerprints = load_all_stores(tmp_path, "Masyu_dataset")
    assert "02_2x2" not in fingerprints["case_id"]
    assert "2x2_0001_9" in fingerprints["case_id"]
    problems = legacy_problems(tmp_path / "Masyu_dataset.json")
    assert "2 2\nw -\n- b" in problems


def test_default_cap_is_500() -> None:
    assert MAX_PER_FILE == 500


def test_shard_prefix() -> None:
    assert shard_prefix("Masyu") == "Masyu_dataset"
    assert shard_prefix("LITS") == "LITS_dataset"


def test_format_and_parse_case_id() -> None:
    cid = format_case_id(8, 8, 1, "5483926")
    assert cid == "8x8_0001_5483926"
    assert parse_case_id(cid) == (8, 8, 1, "5483926")
    dated = format_case_id(30, 30, 3, "2026-08-12")
    assert dated == "30x30_0003_2026-08-12"
    assert parse_case_id(dated) == (30, 30, 3, "2026-08-12")
    assert format_case_id(5, 6, 1222, "N") == "5x6_1222_N"
    assert parse_case_id("size2_5483926") is None


def test_next_seqs_are_per_size() -> None:
    counters = next_seqs({"8x8_0001_1", "8x8_0004_2", "10x10_0002_9", "junk"})
    assert counters[(8, 8)] == 4
    assert counters[(10, 10)] == 2
    assert (6, 6) not in counters


def test_site_ref_from_raw_and_old_id() -> None:
    assert site_ref_from_raw({"puzzle_id": "5483926"}) == "5483926"
    assert site_ref_from_raw({"puzzle_id": "0", "puzzle_date": "2026-08-12"}) == "2026-08-12"
    assert site_ref_from_raw({"puzzle_id": None, "loaded_id": "77"}) == "77"
    assert site_ref_from_raw({}) == "N"
    assert site_ref_from_old_id("size2_5483926") == "5483926"
    assert site_ref_from_old_id("size13_2026-08-12") == "2026-08-12"
    assert site_ref_from_old_id("weird") == "N"
