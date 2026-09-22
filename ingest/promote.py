"""Promote already-formed dataset JSON into the canonical shard corpus."""

from __future__ import annotations

import io
import json
import re
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from cleaners.io import (
    DATA_ROOT,
    REPO_ROOT,
    append_cases,
    cases_legacy_then_shards,
    dataset_path,
    has_dataset,
    list_puzzle_dirs,
    normalize_problem_key,
    shard_paths,
    source_files,
)

_DATASET_FILE = re.compile(r"^(.+)_dataset(?:_(\d{3}))?\.json$")
_PUZZLINK_MARK = "puzz.link/p?"


@dataclass
class PuzzlePromoteReport:
    puzzle: str
    source_cases: int = 0
    added: int = 0
    skipped_problem: int = 0
    skipped_url: int = 0
    skipped_empty: int = 0
    id_renamed: int = 0
    split_monolith: bool = False
    written: list[str] = field(default_factory=list)
    added_ids: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "puzzle": self.puzzle,
            "source_cases": self.source_cases,
            "added": self.added,
            "skipped_problem": self.skipped_problem,
            "skipped_url": self.skipped_url,
            "skipped_empty": self.skipped_empty,
            "id_renamed": self.id_renamed,
            "split_monolith": self.split_monolith,
            "written": self.written,
            "added_ids": self.added_ids,
        }


@dataclass
class SourcePuzzle:
    name: str
    cases: dict[str, dict]


def case_urls(case: dict) -> list[str]:
    urls: list[str] = []
    link = str(case.get("puzzlink_url") or "").strip()
    if link:
        urls.append(link)
    source = str(case.get("source") or "").strip()
    if _PUZZLINK_MARK in source:
        urls.append(source)
    return urls


def allocate_case_id(base: str, used: set[str]) -> tuple[str, bool]:
    if base not in used:
        return base, False
    suffix = 1
    while f"{base}_{suffix}" in used:
        suffix += 1
    return f"{base}_{suffix}", True


def scan_dest_index(
    puzzle_name: str,
    *,
    data_root: Path | None = None,
) -> tuple[set[str], set[str], set[str]]:
    """Return (case_ids, problem_keys, urls) from every dest file."""
    ids: set[str] = set()
    problems: set[str] = set()
    urls: set[str] = set()
    if not has_dataset(puzzle_name, data_root=data_root):
        return ids, problems, urls
    for path in source_files(puzzle_name, data_root=data_root):
        payload = json.loads(path.read_text(encoding="utf-8"))
        for cid, case in (payload.get("data") or {}).items():
            if not isinstance(case, dict):
                continue
            ids.add(str(cid))
            problem = normalize_problem_key(str(case.get("problem") or ""))
            if problem:
                problems.add(problem)
            urls.update(case_urls(case))
    return ids, problems, urls


def _puzzle_name_from_file(path: Path, payload: dict) -> str:
    name = str(payload.get("name") or "").strip()
    if name:
        return name
    match = _DATASET_FILE.fullmatch(path.name)
    if match:
        return match.group(1)
    return path.stem


def _load_json_cases(path: Path) -> tuple[str, dict[str, dict]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    name = _puzzle_name_from_file(path, payload)
    cases: dict[str, dict] = {}
    seen: set[str] = set()
    for cid, case in (payload.get("data") or {}).items():
        if not isinstance(case, dict):
            continue
        problem = normalize_problem_key(str(case.get("problem") or ""))
        if cid in cases or (problem and problem in seen):
            continue
        cases[str(cid)] = case
        if problem:
            seen.add(problem)
    return name, cases


def resolve_source_data_root(path: Path) -> Path:
    """Map a repo root, assets/data, or puzzle dir to an assets/data root."""
    path = path.resolve()
    if (path / "assets" / "data").is_dir():
        return path / "assets" / "data"
    return path


def is_puzzle_dir(path: Path) -> bool:
    if not path.is_dir():
        return False
    parent = path.parent
    return has_dataset(path.name, data_root=parent) and not (path / "assets").is_dir()


def load_source_puzzles(
    source: Path,
    *,
    only: set[str] | None = None,
) -> list[SourcePuzzle]:
    source = source.resolve()
    loaded: list[SourcePuzzle] = []
    if source.is_file():
        name, cases = _load_json_cases(source)
        if only is None or name in only:
            loaded.append(SourcePuzzle(name=name, cases=cases))
        return loaded

    if is_puzzle_dir(source):
        names = [source.name]
        data_root = source.parent
    else:
        data_root = resolve_source_data_root(source)
        names = list_puzzle_dirs(data_root=data_root)

    if only is not None:
        names = [name for name in names if name in only]

    for name in names:
        _label, cases = cases_legacy_then_shards(name, data_root=data_root)
        loaded.append(SourcePuzzle(name=name, cases=cases))
    return loaded


def select_new_cases(
    source_cases: dict[str, dict],
    *,
    dest_ids: set[str],
    dest_problems: set[str],
    dest_urls: set[str],
) -> tuple[list[tuple[str, dict]], PuzzlePromoteReport]:
    report = PuzzlePromoteReport(puzzle="", source_cases=len(source_cases))
    added: list[tuple[str, dict]] = []
    used_ids = set(dest_ids)
    problems = set(dest_problems)
    urls = set(dest_urls)
    for cid, case in source_cases.items():
        problem = normalize_problem_key(str(case.get("problem") or ""))
        if not problem:
            report.skipped_empty += 1
            continue
        case_link_hits = [url for url in case_urls(case) if url in urls]
        if case_link_hits:
            report.skipped_url += 1
            continue
        if problem in problems:
            report.skipped_problem += 1
            continue
        new_id, renamed = allocate_case_id(str(cid), used_ids)
        if renamed:
            report.id_renamed += 1
        added.append((new_id, case))
        used_ids.add(new_id)
        problems.add(problem)
        urls.update(case_urls(case))
        report.added_ids.append(new_id)
    report.added = len(added)
    return added, report


def promote_puzzle(
    source: SourcePuzzle,
    *,
    dest_root: Path,
    write: bool,
) -> PuzzlePromoteReport:
    dest_ids, dest_problems, dest_urls = scan_dest_index(
        source.name, data_root=dest_root
    )
    added, report = select_new_cases(
        source.cases,
        dest_ids=dest_ids,
        dest_problems=dest_problems,
        dest_urls=dest_urls,
    )
    report.puzzle = source.name
    would_split = bool(added) and dataset_path(
        source.name, data_root=dest_root
    ).is_file() and not shard_paths(source.name, data_root=dest_root)
    if not write or not added:
        report.split_monolith = would_split
        return report

    result = append_cases(
        source.name,
        added,
        data_root=dest_root,
        backup=True,
    )
    report.split_monolith = bool(result.split)
    report.written = [path.name for path in result.written]
    return report


def materialize_ref(ref: str, *, repo_root: Path | None = None) -> Path:
    """Extract ``assets/data`` from a git ref into a temporary directory."""
    root = repo_root or REPO_ROOT
    tmp = Path(tempfile.mkdtemp(prefix="puzzlekit-promote-"))
    proc = subprocess.run(
        ["git", "archive", "--format=tar", ref, "assets/data"],
        cwd=root,
        check=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            proc.stderr.decode("utf-8", errors="replace").strip()
            or f"git archive {ref} failed"
        )
    with tarfile.open(fileobj=io.BytesIO(proc.stdout), mode="r:") as archive:
        try:
            archive.extractall(tmp, filter="data")
        except TypeError:
            archive.extractall(tmp)
    return tmp


def iter_reports_to_totals(reports: list[PuzzlePromoteReport]) -> dict[str, int]:
    totals = {
        "puzzles": len(reports),
        "source_cases": 0,
        "added": 0,
        "skipped_problem": 0,
        "skipped_url": 0,
        "skipped_empty": 0,
        "id_renamed": 0,
    }
    for report in reports:
        totals["source_cases"] += report.source_cases
        totals["added"] += report.added
        totals["skipped_problem"] += report.skipped_problem
        totals["skipped_url"] += report.skipped_url
        totals["skipped_empty"] += report.skipped_empty
        totals["id_renamed"] += report.id_renamed
    return totals


def build_batch_report(
    *,
    source_label: str,
    dest_root: Path,
    write: bool,
    reports: list[PuzzlePromoteReport],
) -> dict:
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": source_label,
        "dest": str(dest_root),
        "write": write,
        "puzzles": [report.as_dict() for report in reports],
        "totals": iter_reports_to_totals(reports),
    }


def promote(
    *,
    source: Path,
    dest_root: Path = DATA_ROOT,
    only: set[str] | None = None,
    write: bool = False,
    source_label: str | None = None,
) -> tuple[list[PuzzlePromoteReport], dict]:
    puzzles = load_source_puzzles(source, only=only)
    reports = [
        promote_puzzle(item, dest_root=dest_root, write=write) for item in puzzles
    ]
    batch = build_batch_report(
        source_label=source_label or str(source),
        dest_root=dest_root,
        write=write,
        reports=reports,
    )
    return reports, batch


def refresh_readme_stats() -> None:
    from analytics.res_generator import inject_readme

    inject_readme()
