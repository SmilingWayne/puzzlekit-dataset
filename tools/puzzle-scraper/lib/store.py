from __future__ import annotations

import json
import re
from pathlib import Path

MAX_PER_FILE = 500
_RE_LEGACY_ZERO_ID = re.compile(r"^size\d+_0$")
_RE_INFO_DATE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")
_RE_CASE_ID = re.compile(r"^(\d+)x(\d+)_(\d+)_(\d{4}-\d{2}-\d{2}|N|[0-9]+)$")
_RE_OLD_ID = re.compile(r"^size\d+_(.+)$")
_RE_BLANK_SITE_REF = {None, "", "0"}


def shard_prefix(puzzle_name: str) -> str:
    return f"{puzzle_name}_dataset"


def build_problem(dims: tuple[int, int], cells: list[str]) -> str:
    w, h = dims
    rows = [" ".join(cells[r * w : (r + 1) * w]) for r in range(h)]
    return "\n".join([f"{h} {w}", *rows])


def grid_rows_cols(dims: tuple[int, int]) -> tuple[int, int]:
    """Map site (width, height) to dataset (rows, cols)."""
    width, height = dims
    return height, width


def normalize_problem(problem: str) -> str:
    lines = [line.strip() for line in problem.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(" ".join(line.split()) if line else "" for line in lines).strip()


def format_case_id(rows: int, cols: int, seq: int, site_ref: str) -> str:
    return f"{rows}x{cols}_{seq:04d}_{site_ref}"


def parse_case_id(case_id: str) -> tuple[int, int, int, str] | None:
    match = _RE_CASE_ID.fullmatch(case_id)
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), int(match.group(3)), match.group(4)


def site_ref_from_raw(raw: dict) -> str:
    puzzle_id = raw.get("puzzle_id")
    if puzzle_id not in _RE_BLANK_SITE_REF:
        return str(puzzle_id)
    puzzle_date = raw.get("puzzle_date")
    if puzzle_date:
        return str(puzzle_date)
    loaded_id = raw.get("loaded_id")
    if loaded_id not in _RE_BLANK_SITE_REF:
        return str(loaded_id)
    return "N"


def site_ref_from_old_id(old_id: str) -> str:
    match = _RE_OLD_ID.match(old_id)
    return match.group(1) if match else "N"


def next_seqs(case_ids: set[str] | list[str]) -> dict[tuple[int, int], int]:
    counters: dict[tuple[int, int], int] = {}
    for cid in case_ids:
        parsed = parse_case_id(cid)
        if parsed is None:
            continue
        rows, cols, seq, _ref = parsed
        key = (rows, cols)
        counters[key] = max(counters.get(key, 0), seq)
    return counters


def allocate_case_id(
    rows: int,
    cols: int,
    site_ref: str,
    counters: dict[tuple[int, int], int],
) -> str:
    key = (rows, cols)
    seq = counters.get(key, 0) + 1
    counters[key] = seq
    return format_case_id(rows, cols, seq, site_ref)


def legacy_problems(path: Path) -> set[str]:
    if not path.is_file():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    problems: set[str] = set()
    for case in data.get("data", {}).values():
        problem = case.get("problem") or ""
        if problem:
            problems.add(problem)
            problems.add(normalize_problem(problem))
    return problems


def load_all_stores(out_dir: Path, file_prefix: str) -> dict:
    """Return fingerprints of every already-scraped shard case."""
    fingerprints: dict = {
        "case_id": set(),
        "problem": set(),
        "problem_to_id": {},
        "id_location": {},
    }
    if out_dir.is_dir():
        for path in sorted(out_dir.glob(f"{file_prefix}_*.json")):
            data = json.loads(path.read_text(encoding="utf-8"))
            for cid, case in data.get("data", {}).items():
                problem = case["problem"]
                fingerprints["case_id"].add(cid)
                fingerprints["problem"].add(problem)
                fingerprints["problem"].add(normalize_problem(problem))
                fingerprints["problem_to_id"][problem] = cid
                fingerprints["id_location"][cid] = path
    return fingerprints


def merge_legacy_into_fingerprints(fingerprints: dict, puzzle_name: str, out_dir: Path) -> None:
    for problem in legacy_problems(out_dir / f"{puzzle_name}_dataset.json"):
        fingerprints["problem"].add(problem)


def legacy_zero_case_id(cid: str) -> bool:
    return bool(_RE_LEGACY_ZERO_ID.match(cid))


def infer_date_case_id(legacy_id: str, case: dict) -> str | None:
    """Derive size{N}_{YYYY-MM-DD} from a legacy size{N}_0 entry."""
    match = _RE_INFO_DATE.search(case.get("info", ""))
    if not match:
        return None
    prefix = legacy_id.rsplit("_", 1)[0]
    return f"{prefix}_{match.group(1)}"


def upgrade_legacy_zero_ids(out_dir: Path, file_prefix: str) -> list[tuple[str, str]]:
    """Rename size{N}_0 keys to size{N}_{date} using the date in info."""
    renames: list[tuple[str, str]] = []
    if not out_dir.is_dir():
        return renames

    for path in sorted(out_dir.glob(f"{file_prefix}_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        changed = False
        for cid in list(data.get("data", {})):
            if not legacy_zero_case_id(cid):
                continue
            new_cid = infer_date_case_id(cid, data["data"][cid])
            if not new_cid or new_cid == cid or new_cid in data["data"]:
                continue
            data["data"][new_cid] = data["data"].pop(cid)
            renames.append((cid, new_cid))
            changed = True
        if changed:
            finalize_store(data)
            save_store(path, data)
    return renames


def apply_case_id_upgrades(
    upgrades: list[tuple[str, str, dict]],
    id_location: dict[str, Path],
) -> list[Path]:
    """Replace legacy case ids in-place (old_cid -> new_cid)."""
    touched: dict[Path, dict] = {}
    for old_cid, new_cid, case in upgrades:
        path = id_location.get(old_cid)
        if path is None:
            continue
        if path not in touched:
            touched[path] = json.loads(path.read_text(encoding="utf-8"))
        data = touched[path]
        if old_cid not in data.get("data", {}):
            continue
        data["data"].pop(old_cid, None)
        data["data"][new_cid] = case

    written: list[Path] = []
    for path, data in touched.items():
        finalize_store(data)
        save_store(path, data)
        written.append(path)
    return written


def target_store_path(existing_files: int, out_dir: Path, file_prefix: str) -> Path:
    return out_dir / f"{file_prefix}_{existing_files:03d}.json"


def save_store(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def finalize_store(data: dict) -> None:
    data["count"] = len(data["data"])
    data["count_sol"] = sum(1 for case in data["data"].values() if case.get("solution"))


def store_cases(
    added: list[tuple[int, str, dict]],
    out_dir: Path,
    *,
    name: str,
    file_prefix: str,
) -> list[Path]:
    """Append cases to the newest store file, rolling over at MAX_PER_FILE."""
    written: list[Path] = []
    remaining = list(added)

    newest_path, newest_data = None, None
    if out_dir.is_dir():
        for path in sorted(out_dir.glob(f"{file_prefix}_*.json")):
            newest_path, newest_data = path, json.loads(path.read_text(encoding="utf-8"))

    if newest_data is not None:
        capacity = MAX_PER_FILE - len(newest_data["data"])
        take, remaining = remaining[:capacity], remaining[capacity:]
        if take:
            for _, cid, case in take:
                newest_data["data"][cid] = case
            finalize_store(newest_data)
            save_store(newest_path, newest_data)
            written.append(newest_path)

    existing = len(list(out_dir.glob(f"{file_prefix}_*.json"))) if out_dir.is_dir() else 0
    while remaining:
        take, remaining = remaining[:MAX_PER_FILE], remaining[MAX_PER_FILE:]
        path = target_store_path(existing, out_dir, file_prefix)
        existing += 1
        data = {
            "name": name,
            "count": 0,
            "count_sol": 0,
            "data": {},
        }
        for _, cid, case in take:
            data["data"][cid] = case
        finalize_store(data)
        save_store(path, data)
        written.append(path)
    return written
