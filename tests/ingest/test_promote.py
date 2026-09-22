from __future__ import annotations

import json
from pathlib import Path

from cleaners.io import (
    dataset_path,
    dump_dataset_file,
    file_payload,
    load_dataset,
    shard_path,
)
from ingest.cli import main as ingest_main
from ingest.promote import (
    allocate_case_id,
    load_source_puzzles,
    promote,
    select_new_cases,
)


def _case(cid: str, *, solution: str = "", url: str = "") -> dict:
    payload = {
        "problem": f"2 2\n- -\n- {cid}",
        "solution": solution,
        "source": "https://example.test/",
        "info": "",
    }
    if url:
        payload["puzzlink_url"] = url
    return payload


def test_allocate_case_id_suffixes_on_collision() -> None:
    used = {"a", "a_1"}
    new_id, renamed = allocate_case_id("a", used)
    assert new_id == "a_2"
    assert renamed is True
    kept, renamed = allocate_case_id("b", used)
    assert kept == "b"
    assert renamed is False


def test_select_skips_problem_and_url_keeps_empty_solution() -> None:
    source = {
        "keep": _case("keep"),
        "dup_problem": {
            "problem": "2 2\n- -\n- old",
            "solution": "filled",
            "source": "",
            "info": "",
        },
        "dup_url": _case("other", url="https://puzz.link/p?masyu/1"),
        "empty": {"problem": "", "solution": "", "source": "", "info": ""},
    }
    added, report = select_new_cases(
        source,
        dest_ids={"old"},
        dest_problems={"2 2\n- -\n- old"},
        dest_urls={"https://puzz.link/p?masyu/1"},
    )
    assert [cid for cid, _case in added] == ["keep"]
    assert added[0][1]["solution"] == ""
    assert report.skipped_problem == 1
    assert report.skipped_url == 1
    assert report.skipped_empty == 1
    assert report.added == 1


def test_promote_dry_run_does_not_write(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    dump_dataset_file(
        shard_path("Foo", 0, data_root=dest),
        file_payload("Foo", {"old": _case("old", solution="x")}),
    )
    dump_dataset_file(
        shard_path("Foo", 0, data_root=src),
        file_payload("Foo", {"old": _case("old"), "new": _case("new")}),
    )
    before = shard_path("Foo", 0, data_root=dest).read_bytes()
    reports, batch = promote(source=src, dest_root=dest, write=False)
    assert batch["write"] is False
    assert reports[0].added == 1
    assert reports[0].skipped_problem == 1
    assert shard_path("Foo", 0, data_root=dest).read_bytes() == before
    assert not shard_path("Foo", 1, data_root=dest).is_file()


def test_promote_write_skips_dup_appends_empty_solution(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    first = shard_path("Foo", 0, data_root=dest)
    dump_dataset_file(first, file_payload("Foo", {"old": _case("old", solution="x")}))
    dump_dataset_file(
        shard_path("Foo", 1, data_root=dest),
        file_payload("Foo", {"mid": _case("mid", solution="y")}),
    )
    dump_dataset_file(
        shard_path("Foo", 0, data_root=src),
        file_payload(
            "Foo",
            {
                "old": _case("old", solution="should-not-overwrite"),
                "fresh": _case("fresh"),
            },
        ),
    )
    before = first.read_bytes()
    reports, _batch = promote(source=src, dest_root=dest, write=True)
    assert reports[0].added == 1
    assert first.read_bytes() == before
    loaded = load_dataset("Foo", data_root=dest)
    assert loaded["data"]["old"]["solution"] == "x"
    assert loaded["data"]["fresh"]["solution"] == ""
    assert loaded["count"] == 3
    assert loaded["count_sol"] == 2


def test_promote_renames_colliding_ids(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    dump_dataset_file(
        shard_path("Foo", 0, data_root=dest),
        file_payload("Foo", {"same": _case("dest")}),
    )
    dump_dataset_file(
        shard_path("Foo", 0, data_root=src),
        file_payload("Foo", {"same": _case("incoming")}),
    )
    reports, _batch = promote(source=src, dest_root=dest, write=True)
    assert reports[0].id_renamed == 1
    loaded = load_dataset("Foo", data_root=dest)
    assert set(loaded["data"]) == {"same", "same_1"}
    assert loaded["data"]["same"]["problem"].endswith("dest")
    assert loaded["data"]["same_1"]["problem"].endswith("incoming")


def test_promote_new_puzzle_creates_000(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    dump_dataset_file(
        shard_path("Tapa", 0, data_root=src),
        file_payload("Tapa", {"8x8_0001_1": _case("a")}),
    )
    reports, _batch = promote(source=src, dest_root=dest, write=True)
    assert reports[0].puzzle == "Tapa"
    assert reports[0].added == 1
    assert shard_path("Tapa", 0, data_root=dest).is_file()
    assert not dataset_path("Tapa", data_root=dest).is_file()
    loaded = load_dataset("Tapa", data_root=dest)
    assert list(loaded["data"]) == ["8x8_0001_1"]


def test_load_source_single_json_file(tmp_path: Path) -> None:
    path = tmp_path / "dump.json"
    dump_dataset_file(path, file_payload("Bar", {"a": _case("a"), "b": _case("b")}))
    loaded = load_source_puzzles(path)
    assert [item.name for item in loaded] == ["Bar"]
    assert list(loaded[0].cases) == ["a", "b"]


def test_cli_promote_dry_run(tmp_path: Path, monkeypatch, capsys) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    dump_dataset_file(
        shard_path("Foo", 0, data_root=dest),
        file_payload("Foo", {"old": _case("old")}),
    )
    dump_dataset_file(
        shard_path("Foo", 0, data_root=src),
        file_payload("Foo", {"new": _case("new")}),
    )
    monkeypatch.setattr("ingest.cli.REPORT_DIR", tmp_path / "reports")
    before = shard_path("Foo", 0, data_root=dest).read_bytes()
    code = ingest_main(
        [
            "promote",
            "--source",
            str(src),
            "--data-root",
            str(dest),
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert "Dry-run only" in captured.out
    assert shard_path("Foo", 0, data_root=dest).read_bytes() == before
    report_file = next((tmp_path / "reports").glob("promote_*.json"))
    payload = json.loads(report_file.read_text())
    assert payload["totals"]["added"] == 1
    assert payload["write"] is False


def test_promote_splits_dest_monolith_on_write(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    src = tmp_path / "src"
    dump_dataset_file(
        dataset_path("Foo", data_root=dest),
        file_payload("Foo", {"a": _case("a"), "b": _case("b")}),
    )
    dump_dataset_file(
        shard_path("Foo", 0, data_root=src),
        file_payload("Foo", {"c": _case("c")}),
    )
    reports, _batch = promote(source=src, dest_root=dest, write=True)
    assert reports[0].split_monolith is True
    assert not dataset_path("Foo", data_root=dest).is_file()
    loaded = load_dataset("Foo", data_root=dest)
    assert list(loaded["data"]) == ["a", "b", "c"]
