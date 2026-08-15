#!/usr/bin/env bash
# Daily puzzle scrape. Invoked by GitHub Actions (and optionally local launchd).
# Dedup in lib/store.py is the catch-up mechanism — re-running the same day
# is safe and should mostly print SKIP.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$REPO_ROOT"

MAX_ATTEMPTS="${SCRAPE_MAX_ATTEMPTS:-3}"
RETRY_SLEEP="${SCRAPE_RETRY_SLEEP:-300}"

run_scraper() {
    local name="$1"
    local script="$2"
    local attempt=1

    echo "=== $name scrape ==="
    while true; do
        if python3 "$script" --write; then
            return 0
        fi
        if [ "$attempt" -ge "$MAX_ATTEMPTS" ]; then
            echo "$name: scrape failed after $MAX_ATTEMPTS attempts" >&2
            return 1
        fi
        echo "$name: attempt $attempt failed, retrying in ${RETRY_SLEEP}s" >&2
        sleep "$RETRY_SLEEP"
        attempt=$((attempt + 1))
    done
}

exit_code=0
run_scraper "Masyu" "tools/puzzle-scraper/bin/scrape_masyu.py" || exit_code=1
run_scraper "Shingoki" "tools/puzzle-scraper/bin/scrape_shingoki.py" || exit_code=1
run_scraper "Shakashaka" "tools/puzzle-scraper/bin/scrape_shakashaka.py" || exit_code=1
exit "$exit_code"
