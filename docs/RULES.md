# Dataset cleaning log — agent output spec

Use this spec whenever you clean a puzzle dataset and append or replace an entry in [`CHANGELOG.md`](./CHANGELOG.md).

---

## Workflow (agent)

1. Read the puzzle-specific cleaning rules (one-off script or task brief).
2. Run cleaning on the target `*_dataset.json` (dry-run first if the change is destructive).
3. Verify: parser accepts new `problem` shape; `pytest` for that puzzle type passes; spot-check `solve()` if applicable.
4. Persist rule logic in library code (`parsers/`, etc.) if the format change is permanent — not only in a deleted script.
5. Write or replace the `## {PuzzleName}` section in `./CHANGELOG.md` using the template below (English field labels, exact order).
6. Delete or archive the one-off cleaner script after merge; keep this log entry as the source of truth.

---

## `CHANGELOG.md` structure

```markdown
# CHANGELOG of dataset

## {PuzzleName}

…one cleaning run per section; re-run replaces the whole section…
```

- **Section title**: folder name or dataset `name` field (e.g. `ABCEndView`).
- **One section per puzzle type** per cleaning run; a new run **overwrites** that section (do not stack conflicting entries).

---

## Required fields (copy in this order)

| Field | Meaning | Format / constraints |
|-------|---------|----------------------|
| **Timestamp (UTC+0)** | When the cleaned JSON was written | `YYYY-MM-DD HH:MM:SS` (UTC, no offset suffix) |
| **Dataset** | Path to the modified file | Repo-relative path in backticks, e.g. `` `assets/data/ABCEndView/ABCEndView_dataset.json` `` |
| **Rules applied** | What changed (human + agent readable) | Short bullet list; name the rule, not only the script file |
| **#.Modify** | Cases whose `problem` (or `solution`) text was altered by cleaning | `{modified} / {input_total}` — only structural/normalization edits, not dedupe |
| **#.Deduplication** | Cases removed as duplicates | Integer; `0` if none |
| **Dedup criterion** | When dedup was used | Always state explicitly, e.g. `` exact string match on `problem`; keep first case in JSON order `` |
| **Stats: `count`** | Final `count` field in dataset root | Integer after cleaning + dedupe |
| **Stats: `count_sol`** | Final `count_sol` field | Integer; count cases with non-empty `solution` unless the project defines otherwise |
| **Have same problem?** | Whether any duplicate `problem` strings existed | `Yes` or `No` |
| **Duplication (kept → removed)** | Duplicate groups | Omit this subsection if **Have same problem?** is `No`. Otherwise list up to 10 groups: `` `{kept_id}` ← [`removed_id`, …] `` |

Optional (add when relevant):

| Field | When |
|-------|------|
| **Errors** | Non-zero failed cases during cleaning; list count + up to 5 example case ids |
| **Notes** | Parser/version bumps, manual exceptions, links to PR/commit |

---

## Markdown template (fill and paste under `## {PuzzleName}`)

```markdown
## {PuzzleName}

- **Timestamp (UTC+0)**: {YYYY-MM-DD HH:MM:SS}
- **Dataset**: `{path/to/dataset.json}`
- **Rules applied**:
  - {Rule 1: e.g. Remove inner m×n grid rows when every cell is `-`.}
  - {Rule 2: optional}
- **#.Modify**: {modified} / {input_total}
- **#.Deduplication**: {removed_count}
- **Dedup criterion**: {exact string match on `problem`; keep first in file order | N/A}
- **Stats: `count`**: {final_count}
- **Stats: `count_sol`**: {final_count_sol}
- **Have same problem?**: {Yes|No}
- **Duplication (kept → removed)**:
  - `{kept_id}` ← [{removed_id}, …]
```

If **Have same problem?** is `No`, delete the **Duplication** subsection entirely (do not write “N/A” under it).

---

## Problem text conventions (shared)

These rules apply across cleaners unless a puzzle-specific script documents an exception.

### Size header (all layouts)

- The **first line** of `problem` (and usually `solution`) always begins with two integers **`m n`** = rows × columns.
- Extra tokens may follow on the same line for some puzzle types; only the **first two** numbers are the grid size.

### Standard layouts

| ID | Name | Line count | Structure | Example puzzles |
|----|------|------------|-----------|-----------------|
| **1.1** | Grid only | `1 + m` | Line 1: `m n …`; lines 2..m+1: grid, **n** space-separated cells per row | Araf |
| **1.2** | Grid + regions | `1 + 2m` | Line 1: `m n …`; lines 2..m+1: clue grid; lines m+2..2m+1: region / 宫 labels | Aqre |

- Rows are separated by a single `\n` (LF), not `\r\n` unless already normalized elsewhere.
- Each grid row must contain exactly **n** non-empty tokens (space-separated).

Invalid shape → **remove** the case (count under **Errors**, not **#.Modify**).

Implementations: `validate_grid_only_problem`, `validate_grid_with_regions_problem` in [`lib.py`](./lib.py).

### Compact row endings (default)

Between rows, `\n` must immediately follow the last cell token — **no trailing spaces** before the newline.

- Bad: `` `5 5 5 \n4 4 4` `` (space before `\n`)
- Good: `` `5 5 5\n4 4 4` ``

Apply `compact_line_separators` to `problem` (and `solution` when present) on every clean run. Each case where either field changes counts toward **#.Modify**.

### Dedup (puzzle-specific)

- Document the criterion in **Dedup criterion** (e.g. exact `problem` string after compacting; or clue grid + region partition bijection for Aqre).
- Keep the **first** case in JSON `data` key order.

### Puzzle-specific clue rules (examples)

| Puzzle | Scope | Allowed non-`-` cells | Helpers |
|--------|--------|-------------------------|---------|
| **BalanceLoop** | `problem` grid rows only | `w`, `b`, `w{digits}`, `b{digits}` (prefix); suffix `2w`→`w2` normalized as **#.Modify** | `validate_balanceloop_clue_grid`, `normalize_balanceloop_problem` |
| **Battleship** | `problem`: header + top/left clue rows + optional `m`×`n` board; `solution`: header + `m` board rows | Problem board: `-`, `n,s,w,e,m,o,x` (lowercase); all-`-` board omitted; solution: `-`, `n,s,w,e,m,o`; `x`→`-` | `normalize_battleship_problem`, `normalize_battleship_solution` |

**Battleship layout (problem)** — line 1: `m n` + ship counts (not validated); lines 2–3: column / row clues (`n` and `m` tokens); then 0 or `m` board rows. If every board cell is `-`, drop the `m` rows.

**Battleship layout (solution)** — line 1: same header style; then exactly `m` board rows (no clue rows).

---


## Conventions

- **Modify vs dedupe**: `#.Modify` counts normalization edits on still-kept cases; `#.Deduplication` counts removed case ids only.
- **Order preserved**: dedupe keeps the **first** occurrence in the dataset’s `data` key order; document removed ids explicitly.
- **Counts must match JSON**: `Stats: count` / `count_sol` must equal the root fields in the written file.
- **Language**: field labels stay English as above; rule descriptions may be English or Chinese, but be one language per entry for clarity.

---

## Example (ABCEndView)

```markdown
## ABCEndView

- **Timestamp (UTC+0)**: 2026-05-25 06:38:28
- **Dataset**: `assets/data/ABCEndView/ABCEndView_dataset.json`
- **Rules applied**:
  - Strip trailing m×n grid lines when all cells are `-` (border-only compact `problem`).
  - Dedupe cases with identical `problem` string; keep earliest key in `data`.
- **#.Modify**: 603 / 607
- **#.Deduplication**: 1
- **Dedup criterion**: exact string match on `problem`; keep first in file order
- **Stats: `count`**: 606
- **Stats: `count_sol`**: 606
- **Have same problem?**: Yes
- **Duplication (kept → removed)**:
  - `479_7x7` ← [529_7x7]
```
