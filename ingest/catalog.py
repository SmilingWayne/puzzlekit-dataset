"""Read puzz.link catalog CSV."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CatalogEntry:
    name: str
    puzzle_type: str
    puzz_link_url: str
    author: str = ""
    solves: str = ""
    difficulty: str = ""


def load_catalog(path: Path, *, catalog_types: set[str]) -> list[CatalogEntry]:
    entries: list[CatalogEntry] = []
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            puzzle_type = (row.get("puzzle_type") or "").strip().lower()
            if puzzle_type not in catalog_types:
                continue
            url = (row.get("puzz_link_url") or "").strip()
            if not url:
                continue
            entries.append(
                CatalogEntry(
                    name=(row.get("name") or "").strip(),
                    puzzle_type=puzzle_type,
                    puzz_link_url=url,
                    author=(row.get("author") or "").strip(),
                    solves=(row.get("solves") or "").strip(),
                    difficulty=(row.get("difficulty") or "").strip(),
                )
            )
    return entries
