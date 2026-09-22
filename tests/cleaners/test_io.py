from __future__ import annotations

import json
from pathlib import Path

from cleaners.io import (
    MAX_PER_FILE,
    dataset_path,
    dump_dataset_file,
    file_payload,
    list_puzzle_dirs,
    load_dataset,
    save_dataset,
    shard_path,
    split_monolith_to_shards,
)


def _case(cid: str, *, solution: str = "") -> dict:
    return {
        "problem": f"2 2\n- -\n- {cid}",
        "solution": solution,
        "source": "https://example.test/",
        "info": "",
    }


def test_load_legacy_only(tmp_path: Path) -> None:
    dump_dataset_file(
        dataset_path("Foo", data_root=tmp_path),
        file_payload("Foo", {"02_2x2": _case("a", solution="x")}),
    )
    loaded = load_dataset("Foo", data_root=tmp_path)
    assert loaded["count"] == 1
    assert loaded["count_sol"] == 1
    assert "02_2x2" in loaded["data"]


def test_load_shards_only_and_list_dirs(tmp_path: Path) -> None:
    dump_dataset_file(
        shard_path("Tapa", 0, data_root=tmp_path),
        file_payload("Tapa", {"8x8_0001_1": _case("a")}),
    )
    (tmp_path / "Emptyish").mkdir()
    loaded = load_dataset("Tapa", data_root=tmp_path)
    assert loaded["count"] == 1
    assert list_puzzle_dirs(data_root=tmp_path) == ["Tapa"]


def test_union_prefers_shard_on_problem_dup(tmp_path: Path) -> None:
    problem = "2 2\nw -\n- b"
    dump_dataset_file(
        dataset_path("Masyu", data_root=tmp_path),
        file_payload(
            "Masyu",
            {
                "02_2x2": {
                    "problem": problem,
                    "solution": "se sw\nne nw",
                    "source": "https://janko.at/",
                    "info": "",
                }
            },
        ),
    )
    dump_dataset_file(
        shard_path("Masyu", 0, data_root=tmp_path),
        file_payload(
            "Masyu",
            {
                "2x2_0001_9": {
                    "problem": problem,
                    "solution": "",
                    "source": "https://example.test/",
                    "info": "daily",
                }
            },
        ),
    )
    loaded = load_dataset("Masyu", data_root=tmp_path)
    assert loaded["count"] == 1
    assert list(loaded["data"]) == ["2x2_0001_9"]
    assert loaded["data"]["2x2_0001_9"]["info"] == "daily"


def test_save_legacy_only_rewrites_monolith(tmp_path: Path) -> None:
    path = dataset_path("Foo", data_root=tmp_path)
    dump_dataset_file(path, file_payload("Foo", {"a": _case("a")}))
    cleaned = file_payload("Foo", {"a": _case("a"), "b": _case("b")})
    written = save_dataset("Foo", cleaned, data_root=tmp_path, backup=True)
    assert written == path
    assert path.is_file()
    assert not shard_path("Foo", 0, data_root=tmp_path).is_file()
    assert (tmp_path / "Foo" / "Foo_dataset.json.bak").is_file()


def test_save_does_not_recreate_monolith_when_shards_exist(tmp_path: Path) -> None:
    dump_dataset_file(
        shard_path("Foo", 0, data_root=tmp_path),
        file_payload("Foo", {"a": _case("a")}),
    )
    cleaned = load_dataset("Foo", data_root=tmp_path)
    cleaned["data"]["a"]["info"] = "touched"
    cleaned["data"]["b"] = _case("b")
    written = save_dataset("Foo", cleaned, data_root=tmp_path, backup=False)
    assert written == tmp_path / "Foo"
    assert not dataset_path("Foo", data_root=tmp_path).is_file()
    shard = json.loads(shard_path("Foo", 0, data_root=tmp_path).read_text())
    assert shard["data"]["a"]["info"] == "touched"
    assert "b" in shard["data"]
    assert shard["count"] == 2


def test_save_writes_back_to_original_shard(tmp_path: Path) -> None:
    dump_dataset_file(
        shard_path("Foo", 0, data_root=tmp_path),
        file_payload("Foo", {"a": _case("a"), "b": _case("b")}),
    )
    dump_dataset_file(
        shard_path("Foo", 1, data_root=tmp_path),
        file_payload("Foo", {"c": _case("c")}),
    )
    cleaned = load_dataset("Foo", data_root=tmp_path)
    del cleaned["data"]["b"]
    cleaned["data"]["c"]["info"] = "kept"
    save_dataset("Foo", cleaned, data_root=tmp_path, backup=False)
    first = json.loads(shard_path("Foo", 0, data_root=tmp_path).read_text())
    second = json.loads(shard_path("Foo", 1, data_root=tmp_path).read_text())
    assert list(first["data"]) == ["a"]
    assert first["count"] == 1
    assert second["data"]["c"]["info"] == "kept"
    assert not dataset_path("Foo", data_root=tmp_path).is_file()


def test_save_rolls_new_cases_at_cap(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr("cleaners.io.MAX_PER_FILE", 2)
    dump_dataset_file(
        shard_path("Foo", 0, data_root=tmp_path),
        file_payload("Foo", {"a": _case("a"), "b": _case("b")}),
    )
    cleaned = load_dataset("Foo", data_root=tmp_path)
    cleaned["data"]["c"] = _case("c")
    save_dataset("Foo", cleaned, data_root=tmp_path, backup=False)
    first = json.loads(shard_path("Foo", 0, data_root=tmp_path).read_text())
    second = json.loads(shard_path("Foo", 1, data_root=tmp_path).read_text())
    assert set(first["data"]) == {"a", "b"}
    assert set(second["data"]) == {"c"}


def test_save_new_puzzle_creates_shard_not_monolith(tmp_path: Path) -> None:
    save_dataset("Bar", file_payload("Bar", {"a": _case("a")}), data_root=tmp_path, backup=False)
    assert shard_path("Bar", 0, data_root=tmp_path).is_file()
    assert not dataset_path("Bar", data_root=tmp_path).is_file()


def test_split_monolith_preserves_ids_and_deletes_legacy(tmp_path: Path) -> None:
    items = {f"id{i}": _case(str(i)) for i in range(3)}
    dump_dataset_file(dataset_path("Foo", data_root=tmp_path), file_payload("Foo", items))
    written = split_monolith_to_shards("Foo", data_root=tmp_path, max_per_file=2)
    assert [path.name for path in written] == ["Foo_dataset_000.json", "Foo_dataset_001.json"]
    assert not dataset_path("Foo", data_root=tmp_path).is_file()
    loaded = load_dataset("Foo", data_root=tmp_path)
    assert loaded["count"] == 3
    assert list(loaded["data"]) == list(items)


def test_repack_keeps_legacy_first_on_dup(tmp_path: Path) -> None:
    from cleaners.io import cases_legacy_then_shards, repack_to_shards

    problem = "2 2\nw -\n- b"
    dump_dataset_file(
        dataset_path("Masyu", data_root=tmp_path),
        file_payload(
            "Masyu",
            {"02_2x2": {"problem": problem, "solution": "x", "source": "j", "info": ""}},
        ),
    )
    dump_dataset_file(
        shard_path("Masyu", 0, data_root=tmp_path),
        file_payload(
            "Masyu",
            {
                "2x2_0001_9": {
                    "problem": problem,
                    "solution": "",
                    "source": "d",
                    "info": "daily",
                },
                "8x8_0001_1": _case("fresh"),
            },
        ),
    )
    name, cases = cases_legacy_then_shards("Masyu", data_root=tmp_path)
    assert list(cases) == ["02_2x2", "8x8_0001_1"]
    written = repack_to_shards(name, cases, data_root=tmp_path, max_per_file=10)
    assert [path.name for path in written] == ["Masyu_dataset_000.json"]
    assert not dataset_path("Masyu", data_root=tmp_path).is_file()
    loaded = load_dataset("Masyu", data_root=tmp_path)
    assert list(loaded["data"]) == ["02_2x2", "8x8_0001_1"]
    assert loaded["data"]["02_2x2"]["solution"] == "x"


def test_default_cap_is_500() -> None:
    assert MAX_PER_FILE == 500
