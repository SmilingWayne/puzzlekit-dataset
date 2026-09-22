# AGENTS.md — puzzlekit-dataset

Onboarding for **new contributors and coding agents**. Operator commands and puzzle **text formats** live in [README.md](README.md) (§ Cleaning, § Formats). This file explains **what the repo is**, **where things live**, and **rules that prevent bad edits**.

---

## What this repository is

Public corpus of logic-puzzle instances (~40k cases, 100+ types) for [PuzzleKit](https://github.com/SmilingWayne/puzzlekit) and downstream research.

| You need… | Open… |
|-----------|--------|
| Index of puzzles, stats, how to run cleaners | [README.md](README.md) |
| Human log of past cleaning runs | [docs/CHANGELOG.md](docs/CHANGELOG.md) |
| This orientation | `AGENTS.md` (here) |

**Source of truth for puzzle data:** `assets/data/{PuzzleName}/` — numbered shards `{PuzzleName}_dataset_YYY.json` (500 cases per file, `YYY` from `000`). A leftover `{PuzzleName}_dataset.json` monolith may still exist during migration; do not treat it as a second copy of the same cases.  
**Do not read entire JSON files in bulk** — they are large; spot-check 2–3 cases when unsure.

Legacy one-off ingest may still exist under `crawlers/`. **Current maintenance path:** promote already-formed JSON into shards (`python -m ingest promote`, dry-run first) → register in [`cleaners/registry.py`](cleaners/registry.py) if needed → `python -m cleaners run` (dry-run first). Do not merge the `ingest/daily` git branch into `main`, and do not `git checkout` shard files from that branch over the canonical corpus.

---

## Data model (minimal)

Each dataset file:

- `name`, `count`, `count_sol`, `data` (dict of case id → case)
- Each case: `problem`, `solution` (may be empty), `source`, `info` (often empty), optional `puzzlink_url`

**`problem` / `solution`:** multi-line text. Line 1 is usually `m n` (grid size); further lines depend on puzzle type (see README § Formats). Full schema: [`docs/SCHEMA.md`](docs/SCHEMA.md).

**After a successful clean:** across all shards (plus leftover monolith if present), `count == len(data)` on each file; `count_sol` = cases in that file with non-empty `solution`; rows normalized (no trailing spaces before `\n`).

---

## Repository layout

```
puzzlekit-dataset/
├── README.md              ← public docs + stats table (<!-- INJECT STATS --> block)
├── assets/data/{Puzzle}/  ← datasets
├── cleaners/              ← cleaning package (`python -m cleaners`)
│   ├── cli.py, core.py, registry.py, io.py, report.py
│   └── contracts/         ← layout validators, dedupe, per-pipeline logic
├── tests/cleaners/        ← pytest for contracts
├── docs/CHANGELOG.md      ← cleaning history per puzzle type
├── analytics/res_generator.py  ← inject README stats table (<!-- INJECT STATS -->)
└── crawlers/              ← legacy ingest (avoid for new cleaning logic)
```

Use `cleaners/` (plural), not `cleaner/` if a singular stub still exists.

---

## Cleaning system (how it fits together)

One workflow for all registered types:

```
load JSON → normalize text → validate layout → dedupe → report → optional --write
```

- Entry: `python -m cleaners` — full command list in **README § Cleaning**.
- **Default: dry-run** — no changes under `assets/` unless `--write` (creates `*.json.bak` first).
- Which puzzle uses which rules: [`cleaners/registry.py`](cleaners/registry.py) → `PUZZLE_REGISTRY` and layout dicts (`REGION_LAYOUTS`, `RIM_LAYOUTS`, `EXT_LAYOUTS`, …).
- README **Pipeline** column should match registry (refresh table: `python analytics/res_generator.py`).

### Pipeline cheat sheet

| Pipeline | Typical `problem` shape | Dedup (short) |
|----------|-------------------------|---------------|
| `base` | `1 + m` clue grid | Exact normalized `problem` string |
| `region` | `1 + m` regions only, or `1 + 2m` clues + regions | Exact header (+ clues if any) + region partition isomorphism |
| `rim` | header + 2 or 4 edge rows + optional body | Exact header + edges + body per `RIM_LAYOUTS` |
| `ext` | non-standard row layout | Per `EXT_LAYOUTS` (exact header + body rows) |
| `s1`, `s2`, `s3` | dedicated special layouts | Per puzzle in registry (e.g. Nonogram, Thermometer, ConsecutiveSudoku) |
| *(unregistered)* | — | Skipped by `run --all`; **no automatic deletes** |

**Critical:** Do not guess layout from line counts alone. Wrong registration → valid cases removed as “invalid”. When unsure: read 3 sample `problem` strings, compare README § Formats + registry, then choose or extend a pipeline.

**Puzzle text semantics** (margin order, `-`, regions, special tokens): README § Formats — not duplicated here.

---

## Typical agent workflows

### Promote harvest JSON into shards

```bash
python -m ingest promote --from-ref origin/ingest/daily
python -m ingest promote --from-ref origin/ingest/daily --write --stats
```

```bash
python -m cleaners run --puzzle YourPuzzle          # dry-run
python -m cleaners run --puzzle YourPuzzle --changelog
python -m cleaners run --puzzle YourPuzzle --write  # only after review
```

### Promote harvest JSON into shards

```bash
python -m ingest promote --from-ref origin/ingest/daily
python -m ingest promote --from-ref origin/ingest/daily --write --stats
```

### Register an existing layout family

1. Spot-check on-disk `problem` structure.
2. Add name to `_BASE_PUZZLES`, `REGION_LAYOUTS`, `RIM_LAYOUTS`, `EXT_LAYOUTS`, or a special `s*` entry in [`cleaners/registry.py`](cleaners/registry.py).
3. `pytest tests/cleaners/` → dry-run → `--write` if metrics OK → update [`docs/CHANGELOG.md`](docs/CHANGELOG.md) with `--changelog` output.

### New layout family (rare)

Add contract module (mirror [`cleaners/contracts/region_layout.py`](cleaners/contracts/region_layout.py) or [`rim.py`](cleaners/contracts/rim.py)), wire `_PIPELINE_CONFIG` + `get_pipeline_config()`, add tests.

### Batch health check

```bash
python -m cleaners run --all --quiet --summary
```

Only **registered** puzzles run.

---

## Reports and changelog vocabulary

Machine reports: `cleaners/reports/{timestamp}_{Puzzle}.json` (usually gitignored).

When reading reports or CHANGELOG entries:

| Term | Meaning |
|------|---------|
| **#.Modify** | Normalization changed text on cases that were kept |
| **#.Deduplication** | Duplicate case ids removed |
| **Invalid** | Removed because layout validation failed |
| Dedupe order | Keeps **first** case in JSON `data` key order |

`--changelog` prints a ready-made section for `docs/CHANGELOG.md`.

---

## Safety rules (read before editing data)

1. **Dry-run before `--write`** on production JSON under `assets/`.
2. **Do not register** a puzzle under `base` / `region` / `rim` unless its files match that validator.
3. **Do not commit** large `cleaners/reports/*.json` batches unless the project explicitly wants them.
4. **Only create git commits when the user asks.**
5. Avoid loading full `assets/data/**/*.json` into context — sample ids only.

README rows with Pipeline `-` or missing folders: no automated cleaning until modeled.

---

## Where to drill deeper (code)

| Topic | Location |
|-------|----------|
| CLI | [`cleaners/cli.py`](cleaners/cli.py) |
| Main loop | [`cleaners/core.py`](cleaners/core.py) |
| Puzzle → pipeline | [`cleaners/registry.py`](cleaners/registry.py) |
| Grid normalization | [`cleaners/contracts/normalization.py`](cleaners/contracts/normalization.py) |
| Region / rim logic | [`cleaners/contracts/region_layout.py`](cleaners/contracts/region_layout.py), [`rim.py`](cleaners/contracts/rim.py) |
| Tests | [`tests/cleaners/test_pipeline_contracts.py`](tests/cleaners/test_pipeline_contracts.py) |
| Promote | [`ingest/promote.py`](ingest/promote.py), [`ingest/cli.py`](ingest/cli.py) |

Optional future work (not required for basic tasks): solver/parser validation against PuzzleKit; filling empty `solution` fields after uniqueness checks.

**Promote (no solver):** copy new cases from any dataset JSON tree (including `origin/ingest/daily`) onto the last dest shard. Empty solutions stay empty; existing dest cases are never rewritten. See [`docs/SCHEMA.md`](docs/SCHEMA.md).

```bash
python -m ingest promote --from-ref origin/ingest/daily
python -m ingest promote --source /path/to/assets/data --puzzle Masyu
python -m ingest promote --from-ref origin/ingest/daily --write --stats
```

Default is dry-run. `--write` appends only; `--stats` refreshes the README table after a write. Do **not** merge `ingest/daily` into `main`.

**Puzz.link catalog ingest (solves):** see [`ingest/`](ingest/). Needs a venv with `puzzlekit` + `ortools` (`requirements-ingest.txt`):

```bash
PYTHONPATH=../puzzlekit/src python -m ingest masyu              # pilot: first 200 catalog rows (default)
PYTHONPATH=../puzzlekit/src python -m ingest masyu --limit 0    # full catalog (after pilot looks good)
PYTHONPATH=../puzzlekit/src python -m ingest masyu --write      # merge into assets
PYTHONPATH=../puzzlekit/src python -m ingest slitherlink --write
```

---

## Quick decision tree

```
Need to understand a puzzle's text format?
  → README § Formats

Need to clean or validate data?
  → README § Cleaning → registry.py for pipeline

Need to fold harvest JSON (ingest/daily or other dumps) into main?
  → `python -m ingest promote` (dry-run first). Never merge `ingest/daily`.

Changing dedupe or layout rules?
  → contracts/ + tests/cleaners/ + dry-run + CHANGELOG

Pipeline column in README stale?
  → python analytics/res_generator.py   (# --stdout to print only)
```
