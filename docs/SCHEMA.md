# Dataset JSON Schema

Canonical storage for puzzle instances under `assets/data/{PuzzleName}/`.

Preferred layout is numbered shards only:

| File | Role |
|------|------|
| `{PuzzleName}_dataset_YYY.json` | Canonical shards. 500 cases per file. `YYY` is a zero-padded index starting at `000`. |
| `{PuzzleName}_dataset.json` | Leftover legacy monolith. Optional during migration; delete after that puzzle is split. Daily ingest never writes this file. |

`count` / `count_sol` on a file describe **that file**, not the whole puzzle. Tools that need a corpus total union all shards (and a leftover monolith if present) in memory.

Daily ingest writes **only** shard files.

## File-level object

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | yes | PascalCase puzzle name (`Masyu`, `Slitherlink`, …) |
| `count` | integer | yes | Number of cases in `data` |
| `count_sol` | integer | yes | Cases with non-empty `solution` |
| `data` | object | yes | Map of case id → case record |

After cleaning or ingest, `count` must equal `len(data)` and `count_sol` must match cases with solutions.

## Case record

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `problem` | string | yes | Multi-line dataset text (line 1: `rows cols`, then grid/clues) |
| `solution` | string | yes* | Same layout family as `problem`; may be empty only while pending solve |
| `source` | string | no | Original provenance URL (e.g. janko.at page). New puzz.link ingest may leave empty. |
| `info` | string | no | Reserved metadata (`""` or JSON string) |
| `fetched_at` | string | no | ISO-8601 timestamp on daily shards |
| `puzzlink_url` | string | no | Community puzz.link URL when known or derivable |

### Daily shard case ids

`{rows}x{cols}_{seq:04d}_{site_ref}`

- `{rows}x{cols}` comes from the `problem` header, not the site `?size=` catalog bucket
- `{seq}` counts up **per size** inside that puzzle's shards
- `{site_ref}` is the site Puzzle ID, or a daily-special date (`YYYY-MM-DD`), or `N` when there is no site identifier

Examples: `8x8_0001_5483926`, `30x30_0003_2026-08-12`, `5x6_1222_N`.

Daily ingest skips a case when the normalized `problem` already exists in any shard **or** in a leftover `{Puzzle}_dataset.json`.

### Conventions

- **Do not** replace `problem` / `solution` text with a puzz.link URL. URLs are pointers; text is the solver-facing canonical body.
- **janko cases**: keep existing `source` and `problem` / `solution`; add `puzzlink_url` when encodable.
- **puzz.link ingest (pilot)**: set `puzzlink_url`; `source` may remain `""` until provenance is curated.
- **Pilot ingest**: default `--limit 200` on first run; use `--limit 0` for full catalog after review.
- **Dedup**: prefer `puzzlink_url` equality, then normalized `problem` text (same rules as `cleaners`).

## Masyu text format

**Problem** — `rows cols` header, then `rows` lines of space-separated tokens:

- `-` empty cell
- `w` white pearl, `b` black pearl

**Solution** — same header, loop directions per cell using `n` `s` `e` `w` combined in **n → s → e → w** order (e.g. south+east → `se`). Non-path cells are `-`.

Example:

```text
6 6
- - - - - -
- - - - - w
...
```

```text
6 6
se sw - - se sw
ns ns - - ns ns
...
```

## Slitherlink text format

**Problem** — `rows cols` header, then `rows` lines of space-separated tokens:

- `-` empty cell
- `0`–`3` clue (number of surrounding loop segments)

**Solution** — same header, then `rows` lines of inside/outside shading:

- `x` cell inside the loop
- `-` cell outside the loop

Example:

```text
10 10
- 1 1 - 1 - - - - 1
- 1 1 - - 1 1 1 1 -
...
```

```text
10 10
- - - - - - - x - -
x x x x x - - x x x
...
```
