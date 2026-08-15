from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parents[2] / "tools" / "puzzle-scraper"
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from lib.health import fetched_date, summarize_kind, validate_store


def _store(cases: dict) -> dict:
    return {
        "name": "Masyu",
        "count": len(cases),
        "count_sol": 0,
        "data": cases,
    }


def test_validate_store_accepts_well_formed_case() -> None:
    data = _store(
        {
            "size2_1": {
                "problem": "2 2\n- -\n- -",
                "solution": "",
                "source": "https://www.puzzle-masyu.com/?size=2",
                "fetched_at": "2026-08-15T01:00:00+00:00",
            }
        }
    )
    assert validate_store(data) == []


def test_validate_store_rejects_count_mismatch() -> None:
    data = _store(
        {
            "size2_1": {
                "problem": "2 2\n- -\n- -",
                "source": "https://example.test/",
            }
        }
    )
    data["count"] = 99
    errors = validate_store(data)
    assert any("count" in item for item in errors)


def test_fetched_date_uses_iso_prefix() -> None:
    assert fetched_date({"fetched_at": "2026-08-15T01:00:00+00:00"}) == "2026-08-15"
    assert fetched_date({}) is None


def test_summarize_kind_counts_today(tmp_path: Path) -> None:
    root = tmp_path
    directory = root / "assets" / "scraped" / "masyu"
    directory.mkdir(parents=True)
    (directory / "masyu_001.json").write_text(
        json.dumps(
            _store(
                {
                    "size2_old": {
                        "problem": "2 2\n- -\n- -",
                        "source": "https://example.test/",
                        "fetched_at": "2026-08-14T01:00:00+00:00",
                    },
                    "size2_new": {
                        "problem": "2 2\nw -\n- -",
                        "source": "https://example.test/",
                        "fetched_at": "2026-08-15T09:00:00+00:00",
                    },
                }
            )
        )
        + "\n",
        encoding="utf-8",
    )
    row = summarize_kind(root, "masyu", "masyu", today="2026-08-15")
    assert row["ok"] is True
    assert row["total_cases"] == 2
    assert row["fetched_today"] == 1
