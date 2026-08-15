# Puzzle scraper toolkit

Shared scrapers for puzzle sites that embed game state in page HTML (`var task`, dims, puzzle ID).

Daily ingest writes to `assets/scraped/` only. It does **not** merge into `assets/data/`.

## Layout

```
tools/puzzle-scraper/
  lib/              fetch, store, runner, health
  sites/            masyu.py, shingoki.py, shakashaka.py
  bin/              scrape_masyu.py, scrape_shingoki.py, scrape_shakashaka.py
  scripts/          health_check.sh, verify_shingoki_write.sh
  run_daily.sh      daily Masyu + Shingoki + Shakashaka
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
```

Write to rolling JSON stores:

```bash
python3 tools/puzzle-scraper/bin/scrape_shingoki.py --write
python3 tools/puzzle-scraper/bin/scrape_masyu.py --write
python3 tools/puzzle-scraper/bin/scrape_shakashaka.py --write
```

Outputs:

- `assets/scraped/masyu/masyu_*.json`
- `assets/scraped/shingoki/shingoki_*.json`
- `assets/scraped/shakashaka/shakashaka_*.json`

`*.jsonl` run logs are gitignored and are not used by the daily catch-up or health checks.

## Deduplication and rolling files

Before writing, every run scans **all** existing `*_NNN.json` files in the output directory and skips a puzzle when either:

1. **`case_id` already exists** — e.g. `size6_8986819`, or `size13_2026-08-12` for daily specials
2. **`problem` text already exists** — same decoded grid even if the site assigned a new ID

Each JSON file holds at most **500** puzzles (`MAX_PER_FILE` in `lib/store.py`). When full, the next run creates `masyu_002.json`, `shingoki_002.json`, etc. Re-running the same day is safe: duplicates print `SKIP`.

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
5. Commit any `assets/scraped/` changes back to `ingest/daily`

`schedule` only fires after this workflow exists on `main`. Until then, push `ingest/daily` and use **Actions → Daily puzzle scrape → Run workflow**.

Local macOS launchd remains optional:

```bash
tools/puzzle-scraper/install_launchd.sh
```

## Adding a new puzzle type

1. Add `sites/<name>.py` implementing `extract`, `build_case`, `make_case_id`, and `SPEC`.
2. Add `bin/scrape_<name>.py` thin entry.
3. Register in `run_daily.sh` and `lib/health.py` (`STORES`).
4. Output directory `assets/scraped/<name>/`.
