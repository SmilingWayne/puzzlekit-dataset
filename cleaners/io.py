"""Load and save puzzle dataset JSON files."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = REPO_ROOT / "assets" / "data"


def dataset_path(puzzle_name: str, *, data_root: Path | None = None) -> Path:
    root = data_root or DATA_ROOT
    return root / puzzle_name / f"{puzzle_name}_dataset.json"


def load_dataset(puzzle_name: str, *, data_root: Path | None = None) -> dict:
    path = dataset_path(puzzle_name, data_root=data_root)
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def save_dataset(
    puzzle_name: str,
    data: dict,
    *,
    data_root: Path | None = None,
    backup: bool = True,
) -> Path:
    path = dataset_path(puzzle_name, data_root=data_root)
    if backup and path.exists():
        shutil.copy2(path, path.with_suffix(".json.bak"))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    return path


def list_puzzle_dirs(*, data_root: Path | None = None) -> list[str]:
    root = data_root or DATA_ROOT
    if not root.is_dir():
        return []
    return sorted(
        entry.name
        for entry in root.iterdir()
        if entry.is_dir() and (entry / f"{entry.name}_dataset.json").is_file()
    )
