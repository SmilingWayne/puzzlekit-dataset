# Puzzle scraper toolkit

Shared scrapers for puzzle sites that embed game state in page HTML (`var task`, dims, puzzle ID).

Daily ingest writes rolling shards under `assets/data/{Puzzle}/{Puzzle}_dataset_YYY.json`. It does **not** modify frozen `{Puzzle}_dataset.json` files.

## Layout

```
tools/puzzle-scraper/
  lib/              fetch, store, runner, health
  sites/            masyu.py, shingoki.py, shakashaka.py, hashi.py, tapa.py, lits.py
  bin/              scrape_masyu.py, scrape_shingoki.py, scrape_shakashaka.py, scrape_hashi.py, scrape_tapa.py, scrape_lits.py
  scripts/          health_check.sh, migrate_scraped_to_shards.py
  run_daily.sh      daily Masyu + Shingoki + Shakashaka + Hashi + Tapa + LITS
  install_launchd.sh  optional macOS fallback
  logs/             local launchd logs (gitignored)

.github/workflows/daily-scrape.yml
```

## Usage

Dry-run (no writes):

```bash
python3 tools/puzzle-scraper/bin/scrape_shingoki.py
python3 tools/puzzle-scraper/bin/scrape_masyu.py --sizes 2 3
python3 tools/puzzle-scraper/bin/scrape_shakashaka.py
python3 tools/puzzle-scraper/bin/scrape_hashi.py
python3 tools/puzzle-scraper/bin/scrape_tapa.py
python3 tools/puzzle-scraper/bin/scrape_lits.py
```

Write to rolling JSON stores:

```bash
python3 tools/puzzle-scraper/bin/scrape_shingoki.py --write
python3 tools/puzzle-scraper/bin/scrape_masyu.py --write
python3 tools/puzzle-scraper/bin/scrape_shakashaka.py --write
python3 tools/puzzle-scraper/bin/scrape_hashi.py --write
python3 tools/puzzle-scraper/bin/scrape_tapa.py --write
python3 tools/puzzle-scraper/bin/scrape_lits.py --write
```

Outputs (500 cases per file, index from `000`):

- `assets/data/Masyu/Masyu_dataset_YYY.json`
- `assets/data/Shingoki/Shingoki_dataset_YYY.json`
- `assets/data/Shakashaka/Shakashaka_dataset_YYY.json`
- `assets/data/Hashi/Hashi_dataset_YYY.json`
- `assets/data/Tapa/Tapa_dataset_YYY.json`
- `assets/data/LITS/LITS_dataset_YYY.json`

Case ids: `{rows}x{cols}_{seq:04d}_{sitePuzzleId|YYYY-MM-DD|N}`. `*.jsonl` run logs are gitignored.

## Deduplication and rolling files

Before writing, every run scans **all** existing `{Puzzle}_dataset_YYY.json` shards and the frozen `{Puzzle}_dataset.json` (if present) and skips a puzzle when the normalized **`problem`** already exists.

Each JSON file holds at most **500** puzzles (`MAX_PER_FILE` in `lib/store.py`). When full, the next run creates `_001.json`, `_002.json`, etc. Re-running the same day is safe: duplicates print `SKIP`.

## Health check

```bash
tools/puzzle-scraper/scripts/health_check.sh --ci   # store JSON only (GitHub Actions)
tools/puzzle-scraper/scripts/health_check.sh          # + local launchd (macOS)
tools/puzzle-scraper/scripts/health_check.sh --probe  # + dry-run one page per site
```

Offline tests:

```bash
python3 -m pytest tests/puzzle_scraper -q
```

## GitHub Actions

`.github/workflows/daily-scrape.yml` runs at 01:00 and 11:00 UTC (09:00 / 19:00 CST):

1. Checkout `ingest/daily`
2. Run decode/store/health unit tests
3. Run `run_daily.sh`
4. Validate rolling JSON stores
5. Commit shard files (`*_dataset_YYY.json` only) back to `ingest/daily`

`schedule` only fires after this workflow exists on `main`. Cron reads the YAML on `main`; scripts come from `ingest/daily`.

Set repository variable `DAILY_SCRAPE_PAUSE` to `true` to skip **scheduled** runs (the job is skipped, not failed). **Run workflow** still executes so a migration window can be verified. Unset the variable or set it to anything other than `true` to resume cron.

Local macOS launchd remains optional:

```bash
tools/puzzle-scraper/install_launchd.sh
```

## Adding a new puzzle type

1. Add `sites/<name>.py` implementing `extract`, `build_case`, and `SPEC` (`output_dir` under `assets/data/{PuzzleName}`, `file_prefix="{PuzzleName}_dataset"`).
2. Add `bin/scrape_<name>.py` thin entry.
3. Register in `run_daily.sh` and `lib/health.py` (`STORES`).
4. Output directory `assets/data/{PuzzleName}/`.
