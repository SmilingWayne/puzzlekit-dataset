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

**Source of truth for puzzle data:** `assets/data/{PuzzleName}/{PuzzleName}_dataset.json`  
**Do not read entire JSON files in bulk** — they are large; spot-check 2–3 cases when unsure.

Legacy one-off ingest may still exist under `crawlers/`. **Current maintenance path:** add/merge data → register in [`cleaners/registry.py`](cleaners/registry.py) if needed → `python -m cleaners run` (dry-run first).

---

## Data model (minimal)

Each dataset file:

- `name`, `count`, `count_sol`, `data` (dict of case id → case)
- Each case: `problem`, `solution` (may be empty), `source`, `info` (often empty), optional `puzzlink_url`

**`problem` / `solution`:** multi-line text. Line 1 is usually `m n` (grid size); further lines depend on puzzle type (see README § Formats). Full schema: [`docs/SCHEMA.md`](docs/SCHEMA.md).

**After a successful clean:** `count == len(data)`; `count_sol` = cases with non-empty `solution`; rows normalized (no trailing spaces before `\n`).

---

## Repository layout

```
puzzlekit-dataset/
├── README.md              ← public docs + stats table (<!-- INJECT STATS --> block)
├── assets/data/{Puzzle}/  ← datasets
├── cleaners/              ← cleaning package (`python -m cleaners`)
│   ├── cli.py, core.py, registry.py, io.py, report.py
│   └── contracts/         ← layout validators, dedupe, per-pipeline logic
├── integrations/           ← pinned external tools (`pzprjs`, `noqx`)
├── src/pipeline/           ← new TypeScript load-solve-write core contracts
├── tools/                  ← integration utilities and MVP pipeline scripts
├── tests/cleaners/        ← pytest for contracts
├── tests/ts/               ← Vitest tests for new TS pipeline infrastructure
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

## Load-solve-write pipeline exploration

This repository is now exploring a durable local pipeline:

```text
load input → normalize/convert → solve → encode dataset text → write JSON
```

The design goal is **replaceable integrations**, not one hard-coded backend. Keep
the dataset JSON schema stable and put external projects behind adapters.

### Current architecture decisions

- Use `pnpm` for JS/TS tooling; this repo has `package.json`, `pnpm-lock.yaml`, `tsconfig.json`, and `vitest.config.ts`.
- Keep `problem` / `solution` as dataset text. Do **not** replace dataset bodies with URLs or Penpa+ blobs.
- Treat `pzprjs` as the authoritative puzz.link parser/checker, but not as the canonical dataset IR.
- Treat Penpa+ as a solver interchange format, especially for `noqx`; do not make Penpa+ the database schema.
- Treat `noqx` as one replaceable `SolverBackend`, not as the pipeline itself.
- The existing Python cleaners remain independent for now. Do not port or entangle them with the MVP load-solve-write work unless explicitly requested.

### External integrations

Pinned upstreams live under `integrations/` and are tracked in
[`integrations/tools.json`](integrations/tools.json).

| Tool | Role | Current pin |
|------|------|-------------|
| `integrations/pzprjs` | puzz.link parse / normalize / answer check | `v0.12.0` |
| `integrations/noqx` | Penpa+ clingo solver backend candidate | `v0.9.0` |

Useful commands:

```bash
pnpm integrations:status
pnpm integrations:verify
```

If an integration has not been checked out:

```bash
git submodule update --init --recursive
```

When upgrading upstreams, checkout the new tag inside the submodule, update
`integrations/tools.json` with the tag and actual `git rev-parse HEAD`, then run:

```bash
pnpm integrations:verify
pnpm test
pnpm typecheck
```

### Current TS pipeline contracts

Core TS modules live in [`src/pipeline/`](src/pipeline/):

| File | Purpose |
|------|---------|
| `ir.ts` | early `DatasetPuzzle` / `DatasetSolution` types |
| `merge.ts` | problem-key normalization and append/merge helpers |
| `noqx.ts` | normalized noqx request/response protocol |
| `noqxClient.ts` | HTTP client for a future noqx sidecar |
| `pzprAdapter.ts` | pzprjs adapter interface and not-configured fallback |
| `solverBackend.ts` | replaceable solver backend registry |
| `runReport.ts` | per-case stage event reporting |

Run TS checks:

```bash
pnpm test
pnpm typecheck
```

### LITS MVP status

The first end-to-end MVP is intentionally narrow and lives in
[`tools/lits-mvp/`](tools/lits-mvp/). It currently does:

```text
puzzlink_crawlers/logs/merged_puzzles.csv
  → filter puzzle_type=lits
  → pzprjs opens puzz.link URL
  → pzprjs getFileData() gives LITS region rows
  → encode dataset problem text
  → Python bridge calls puzzlekit.solve(problem, "lits")
  → encode dataset solution text
  → append to assets/data/LITS/LITS_dataset.json
```

Important: this LITS MVP **does not** go through Penpa+ or `noqx`. It uses
`puzzlekit` as a temporary solver backend because it can directly produce the
existing dataset `solution` text for LITS. This is acceptable for MVP and should
remain replaceable through the `SolverBackend` boundary.

Commands:

```bash
# one-case dry run
pnpm pipeline:lits:mvp -- --limit 1 --time-limit 20

# actually append to assets/data/LITS/LITS_dataset.json
pnpm pipeline:lits:mvp -- --limit 1 --time-limit 20 --write
```

The Python bridge expects a local venv with ingest deps:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e ../puzzlekit ortools pyyaml typeguard
```

`pzprjs` must be built before Node can `require()` it:

```bash
pnpm --dir integrations/pzprjs install
pnpm --dir integrations/pzprjs build
```

Generated dependency folders and build outputs inside integrations should not be
committed unless explicitly requested.

### Known format/solver caveats

- `puzzlekit.decode()` currently does not support LITS puzz.link URLs, so the LITS MVP uses `pzprjs` file data instead.
- `noqx` is strong when given Penpa+ input. Its built-in puzz.link path relies on Penpa+/Playwright (`imp(url, true)` then `exp()`), which is too heavy to assume as the default batch path until wrapped as a long-lived adapter.
- A future Penpa+ adapter is useful, but Penpa+ should be treated as an external interchange format, not the dataset's canonical model.
- For each puzzle type, prefer a tested route map over a forced universal path. Example routes may differ: `puzz.link → pzprjs → dataset text → puzzlekit`, or `puzz.link/Penpa+ → Penpa adapter → noqx`.

---

## Typical agent workflows

### Inspect or clean one puzzle

```bash
python -m cleaners run --puzzle YourPuzzle          # dry-run
python -m cleaners run --puzzle YourPuzzle --changelog
python -m cleaners run --puzzle YourPuzzle --write  # only after review
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

### Run the current LITS MVP

```bash
pnpm pipeline:lits:mvp -- --limit 1             # dry-run
pnpm pipeline:lits:mvp -- --limit 1 --write     # append one case
```

This MVP intentionally skips dedupe/cleaner checks. Use small limits and inspect
the JSON diff before larger writes.

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
6. For new load-solve-write scripts, default to dry-run and expose explicit `--write`.
7. Keep solver backends replaceable. Do not call `noqx`, `puzzlekit`, or Penpa+ directly from generic pipeline code without an adapter boundary.

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
| TS pipeline contracts | [`src/pipeline/`](src/pipeline/) |
| Integration pins/tools | [`integrations/`](integrations/), [`tools/integrations/`](tools/integrations/) |
| LITS MVP | [`tools/lits-mvp/`](tools/lits-mvp/), [`tests/ts/lits-mvp.test.ts`](tests/ts/lits-mvp.test.ts) |

Optional future work (not required for basic tasks): solver/parser validation against PuzzleKit; unified ingest beyond `crawlers/`.

**Puzz.link ingest:** see [`ingest/`](ingest/) and [`docs/SCHEMA.md`](docs/SCHEMA.md). Run from repo root with a venv that has `puzzlekit` + `ortools` (see `requirements-ingest.txt`). Example:

```bash
PYTHONPATH=../puzzlekit/src python -m ingest masyu              # pilot: first 200 catalog rows (default)
PYTHONPATH=../puzzlekit/src python -m ingest masyu --limit 0    # full catalog (after pilot looks good)
PYTHONPATH=../puzzlekit/src python -m ingest masyu --write      # merge into assets
PYTHONPATH=../puzzlekit/src python -m ingest slitherlink --write
python -m cleaners run --puzzle Masyu --write
```

---

## Quick decision tree

```
Need to understand a puzzle's text format?
  → README § Formats

Need to clean or validate data?
  → README § Cleaning → registry.py for pipeline

Need to run the experimental LITS load-solve-write MVP?
  → pnpm pipeline:lits:mvp -- --limit 1

Need to inspect external parser/solver versions?
  → pnpm integrations:status && pnpm integrations:verify

Changing dedupe or layout rules?
  → contracts/ + tests/cleaners/ + dry-run + CHANGELOG

Pipeline column in README stale?
  → python analytics/res_generator.py   (# --stdout to print only)
```
