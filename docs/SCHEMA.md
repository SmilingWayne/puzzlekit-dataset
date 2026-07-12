# Dataset JSON Schema

Canonical storage for puzzle instances under `assets/data/{PuzzleName}/{PuzzleName}_dataset.json`.

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
| `puzzlink_url` | string | no | Community puzz.link URL when known or derivable |

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
