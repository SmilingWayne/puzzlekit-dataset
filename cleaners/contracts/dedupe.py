"""Dedupe key helpers for puzzle dataset cleaning."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Hashable

from cleaners.contracts.normalization import split_tokens


RegionKey = tuple[tuple[str, ...], ...]

def exact_problem_key(problem: str) -> str:
    """Use the fully normalized problem string as the dedupe key."""

    return problem


def canonical_region_rows(
    rows: list[str],
    *,
    hole_tokens: frozenset[str] | None = None,
    hole_token: str = "@",
) -> RegionKey:
    """Canonicalize region labels while preserving hole positions.

    Labels not in ``hole_tokens`` are considered region identifiers and are
    relabeled by the sorted cells in each region. Hole tokens are not treated
    as regions, but their positions (and literal token) remain part of the key.
    """

    tokens = hole_tokens if hole_tokens is not None else frozenset({hole_token})

    grid = [split_tokens(row) for row in rows]
    if not grid:
        return ()

    groups: dict[str, list[tuple[int, int]]] = defaultdict(list)
    canonical: list[list[str]] = []
    for i, row in enumerate(grid):
        canonical_row: list[str] = []
        for j, cell in enumerate(row):
            if cell in tokens:
                canonical_row.append(cell)
            else:
                groups[cell].append((i, j))
                canonical_row.append("")
        canonical.append(canonical_row)

    sorted_groups = sorted(
        (tuple(sorted(cells)) for cells in groups.values()),
        key=lambda cells: cells[0],
    )
    for idx, cells in enumerate(sorted_groups, start=1):
        label = str(idx)
        for i, j in cells:
            canonical[i][j] = label

    return tuple(tuple(row) for row in canonical)


def group_duplicate_keys(items: list[tuple[str, Hashable]]) -> dict[str, list[str]]:
    """Return kept id -> removed ids for repeated keys."""

    seen: dict[Hashable, str] = {}
    groups: dict[str, list[str]] = defaultdict(list)
    for case_id, key in items:
        if key in seen:
            groups[seen[key]].append(case_id)
        else:
            seen[key] = case_id
    return dict(groups)
