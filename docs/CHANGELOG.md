# Changelog of dataset

Cleaning log entries follow [`changelog.md`](./changelog).

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
- **Duplication (kept ← removed)**:
  - `479_7x7` ← [529_7x7]
