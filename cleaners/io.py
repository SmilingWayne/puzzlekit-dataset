"""Load and save puzzle dataset JSON (legacy monolith and 500-case shards)."""

from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "assets" / "data"

MAX_PER_FILE = 500
_SHARD_NAME = re.compile(r"^(.+)_dataset_(\d{3})\.json$")


def puzzle_dir(puzzle_name: str, *, data_root: Path | None = None) -> Path:
    return (data_root or DATA_ROOT) / puzzle_name


def dataset_path(puzzle_name: str, *, data_root: Path | None = None) -> Path:
    """Legacy monolith path. May be absent after shard migration."""
    return puzzle_dir(puzzle_name, data_root=data_root) / f"{puzzle_name}_dataset.json"


def shard_path(puzzle_name: str, index: int, *, data_root: Path | None = None) -> Path:
    return puzzle_dir(puzzle_name, data_root=data_root) / f"{puzzle_name}_dataset_{index:03d}.json"


def shard_paths(puzzle_name: str, *, data_root: Path | None = None) -> list[Path]:
    directory = puzzle_dir(puzzle_name, data_root=data_root)
    if not directory.is_dir():
        return []
    found: list[tuple[int, Path]] = []
    for path in directory.iterdir():
        match = _SHARD_NAME.fullmatch(path.name)
        if match and match.group(1) == puzzle_name and path.is_file():
            found.append((int(match.group(2)), path))
    found.sort(key=lambda item: item[0])
    return [path for _index, path in found]


def dataset_display_path(puzzle_name: str, *, data_root: Path | None = None) -> Path:
    """Changelog / report path: puzzle directory when shards exist, else monolith."""
    if shard_paths(puzzle_name, data_root=data_root):
        return puzzle_dir(puzzle_name, data_root=data_root)
    return dataset_path(puzzle_name, data_root=data_root)


def source_files(puzzle_name: str, *, data_root: Path | None = None) -> list[Path]:
    """Legacy monolith first (if present), then numbered shards."""
    files: list[Path] = []
    legacy = dataset_path(puzzle_name, data_root=data_root)
    if legacy.is_file():
        files.append(legacy)
    files.extend(shard_paths(puzzle_name, data_root=data_root))
    return files


def has_dataset(puzzle_name: str, *, data_root: Path | None = None) -> bool:
    return bool(source_files(puzzle_name, data_root=data_root))


def list_puzzle_dirs(*, data_root: Path | None = None) -> list[str]:
    root = data_root or DATA_ROOT
    if not root.is_dir():
        return []
    return sorted(
        entry.name
        for entry in root.iterdir()
        if entry.is_dir() and has_dataset(entry.name, data_root=root)
    )


def _load_json(path: Path) -> dict:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_dataset_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def normalize_problem_key(problem: str) -> str:
    lines = [
        line.strip()
        for line in problem.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    ]
    return "\n".join(" ".join(line.split()) if line else "" for line in lines).strip()


def count_sol(cases: dict) -> int:
    return sum(1 for case in cases.values() if str(case.get("solution", "")).strip())


def file_payload(name: str, cases: dict) -> dict:
    return {
        "name": name,
        "count": len(cases),
        "count_sol": count_sol(cases),
        "data": cases,
    }


def union_cases(
    puzzle_name: str,
    *,
    data_root: Path | None = None,
) -> tuple[str, dict[str, dict]]:
    """Merge legacy + shards. Later files win on case id and normalized problem."""
    files = source_files(puzzle_name, data_root=data_root)
    if not files:
        raise FileNotFoundError(
            f"No dataset for {puzzle_name!r}: expected "
            f"{dataset_path(puzzle_name, data_root=data_root).name} or "
            f"{puzzle_name}_dataset_YYY.json"
        )
    union: dict[str, dict] = {}
    seen_problems: dict[str, str] = {}
    name = puzzle_name
    for path in files:
        payload = _load_json(path)
        name = str(payload.get("name") or name)
        for cid, case in (payload.get("data") or {}).items():
            if not isinstance(case, dict):
                continue
            problem_key = normalize_problem_key(str(case.get("problem") or ""))
            if problem_key:
                old_id = seen_problems.get(problem_key)
                if old_id is not None and old_id != cid:
                    union.pop(old_id, None)
            union[cid] = case
            if problem_key:
                seen_problems[problem_key] = cid
    return name, union


def load_dataset(puzzle_name: str, *, data_root: Path | None = None) -> dict:
    name, cases = union_cases(puzzle_name, data_root=data_root)
    return file_payload(name, cases)


def _serialized(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"


def _write_if_changed(path: Path, payload: dict, *, backup: bool) -> bool:
    text = _serialized(payload)
    if path.is_file() and path.read_text(encoding="utf-8") == text:
        return False
    if backup and path.is_file():
        shutil.copy2(path, path.with_suffix(path.suffix + ".bak"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return True


def _next_shard_index(paths: list[Path], puzzle_name: str) -> int:
    highest = -1
    for path in paths:
        match = _SHARD_NAME.fullmatch(path.name)
        if match and match.group(1) == puzzle_name:
            highest = max(highest, int(match.group(2)))
    return highest + 1


def save_dataset(
    puzzle_name: str,
    data: dict,
    *,
    data_root: Path | None = None,
    backup: bool = True,
) -> Path:
    """Write cases back to their home files; append new cases onto shards.

    If only a legacy monolith exists, rewrite that file (pre-migration).
    If any shards exist, never recreate a monolith for new cases.
    If neither exists, create ``{name}_dataset_000.json``.
    """
    directory = puzzle_dir(puzzle_name, data_root=data_root)
    existing_shards = shard_paths(puzzle_name, data_root=data_root)
    legacy = dataset_path(puzzle_name, data_root=data_root)
    cases = dict(data.get("data") or {})
    name = str(data.get("name") or puzzle_name)

    if not existing_shards:
        if legacy.is_file():
            _write_if_changed(legacy, file_payload(name, cases), backup=backup)
            return legacy
        remaining = list(cases.items())
        if not remaining:
            dump_dataset_file(
                shard_path(puzzle_name, 0, data_root=data_root),
                file_payload(name, {}),
            )
            return directory
        index = 0
        while remaining:
            take, remaining = remaining[:MAX_PER_FILE], remaining[MAX_PER_FILE:]
            dump_dataset_file(
                shard_path(puzzle_name, index, data_root=data_root),
                file_payload(name, dict(take)),
            )
            index += 1
        return directory

    file_order: list[Path] = []
    if legacy.is_file():
        file_order.append(legacy)
    file_order.extend(existing_shards)

    homes: dict[str, Path] = {}
    for path in file_order:
        payload = _load_json(path)
        for cid in payload.get("data") or {}:
            homes[cid] = path

    buckets: dict[Path, dict[str, dict]] = {path: {} for path in file_order}
    new_cases: list[tuple[str, dict]] = []
    for cid, case in cases.items():
        home = homes.get(cid)
        if home is not None:
            buckets[home][cid] = case
        else:
            new_cases.append((cid, case))

    for path in file_order:
        _write_if_changed(path, file_payload(name, buckets[path]), backup=backup)

    last = existing_shards[-1]
    last_cases = buckets[last]
    capacity = MAX_PER_FILE - len(last_cases)
    take, remaining = new_cases[: max(capacity, 0)], new_cases[max(capacity, 0) :]
    if take:
        for cid, case in take:
            last_cases[cid] = case
        _write_if_changed(last, file_payload(name, last_cases), backup=backup)

    next_index = _next_shard_index(existing_shards, puzzle_name)
    while remaining:
        take, remaining = remaining[:MAX_PER_FILE], remaining[MAX_PER_FILE:]
        path = shard_path(puzzle_name, next_index, data_root=data_root)
        next_index += 1
        dump_dataset_file(path, file_payload(name, dict(take)))

    return directory


def split_monolith_to_shards(
    puzzle_name: str,
    *,
    data_root: Path | None = None,
    max_per_file: int = MAX_PER_FILE,
) -> list[Path]:
    """Rewrite a legacy monolith as numbered shards and delete the monolith."""
    legacy = dataset_path(puzzle_name, data_root=data_root)
    if not legacy.is_file():
        raise FileNotFoundError(legacy)
    payload = _load_json(legacy)
    name = str(payload.get("name") or puzzle_name)
    items = list((payload.get("data") or {}).items())
    written: list[Path] = []
    remaining = items
    index = 0
    if not remaining:
        path = shard_path(puzzle_name, 0, data_root=data_root)
        dump_dataset_file(path, file_payload(name, {}))
        written.append(path)
    while remaining:
        take, remaining = remaining[:max_per_file], remaining[max_per_file:]
        path = shard_path(puzzle_name, index, data_root=data_root)
        dump_dataset_file(path, file_payload(name, dict(take)))
        written.append(path)
        index += 1
    legacy.unlink()
    return written


def cases_legacy_then_shards(
    puzzle_name: str,
    *,
    data_root: Path | None = None,
) -> tuple[str, dict[str, dict]]:
    """First-wins union: leftover monolith, then shards (skip duplicate problems)."""
    files = source_files(puzzle_name, data_root=data_root)
    if not files:
        raise FileNotFoundError(puzzle_name)
    cases: dict[str, dict] = {}
    seen: set[str] = set()
    name = puzzle_name
    skipped = 0
    for path in files:
        payload = _load_json(path)
        name = str(payload.get("name") or name)
        for cid, case in (payload.get("data") or {}).items():
            if not isinstance(case, dict):
                continue
            problem_key = normalize_problem_key(str(case.get("problem") or ""))
            if cid in cases or (problem_key and problem_key in seen):
                skipped += 1
                continue
            cases[cid] = case
            if problem_key:
                seen.add(problem_key)
    _ = skipped
    return name, cases


def repack_to_shards(
    puzzle_name: str,
    cases: dict[str, dict],
    *,
    name: str | None = None,
    data_root: Path | None = None,
    max_per_file: int = MAX_PER_FILE,
) -> list[Path]:
    """Delete existing dataset files and write a fresh 000-based shard sequence."""
    for path in list(source_files(puzzle_name, data_root=data_root)):
        path.unlink()
    label = name or puzzle_name
    remaining = list(cases.items())
    written: list[Path] = []
    index = 0
    if not remaining:
        path = shard_path(puzzle_name, 0, data_root=data_root)
        dump_dataset_file(path, file_payload(label, {}))
        return [path]
    while remaining:
        take, remaining = remaining[:max_per_file], remaining[max_per_file:]
        path = shard_path(puzzle_name, index, data_root=data_root)
        dump_dataset_file(path, file_payload(label, dict(take)))
        written.append(path)
        index += 1
    return written

