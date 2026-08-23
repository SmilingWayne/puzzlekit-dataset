#!/usr/bin/env bash
# Health check for puzzle-scraper stores and (optionally) local launchd.
# Usage: tools/puzzle-scraper/scripts/health_check.sh [--ci] [--probe]
#   --ci     skip macOS launchd/helper; used by GitHub Actions
#   --probe  dry-run one page per site
set -euo pipefail

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:${PATH:-}"
PYTHON="$(command -v python3)"

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

CI_MODE=false
PROBE=false
for arg in "$@"; do
    case "$arg" in
        --ci) CI_MODE=true ;;
        --probe) PROBE=true ;;
        *) echo "unknown argument: $arg" >&2; exit 2 ;;
    esac
done

if [ "${CI:-}" = "true" ]; then
    CI_MODE=true
fi

LABEL="com.puzzlekit.puzzle-scraper"

section() { echo ""; echo "=== $1 ==="; }

if [ "$CI_MODE" = false ]; then
    section "launchd"
    if command -v launchctl >/dev/null 2>&1 && launchctl print "gui/$(id -u)/$LABEL" >/dev/null 2>&1; then
        launchctl list 2>/dev/null | grep -F "$LABEL" || true
    else
        echo "NOT LOADED — run: tools/puzzle-scraper/install_launchd.sh"
    fi

    section "helper app"
    HELPER="$HOME/Library/Application Support/PuzzleKit/puzzle-scraper.app"
    if [ -x "$HELPER/Contents/MacOS/puzzle-scraper-helper" ]; then
        echo "OK $HELPER"
    else
        echo "MISSING — run install_launchd.sh"
    fi

    section "runtime logs (tail)"
    for f in tools/puzzle-scraper/logs/daily.out.log tools/puzzle-scraper/logs/daily.err.log; do
        echo "--- $f ---"
        if [ -f "$f" ]; then tail -5 "$f"; else echo "(no file yet)"; fi
    done
fi

section "store health"
PYTHONPATH="$REPO_ROOT/tools/puzzle-scraper" "$PYTHON" -m lib.health
health_status=$?

if [ "$PROBE" = true ]; then
    section "network probe (dry-run)"
    "$PYTHON" tools/puzzle-scraper/bin/scrape_shingoki.py --sizes 0 --delay-min 0 --delay-max 0
    "$PYTHON" tools/puzzle-scraper/bin/scrape_shakashaka.py --sizes 0 --delay-min 0 --delay-max 0
    "$PYTHON" tools/puzzle-scraper/bin/scrape_masyu.py --sizes 2 --delay-min 0 --delay-max 0
    "$PYTHON" tools/puzzle-scraper/bin/scrape_hashi.py --sizes 2 --delay-min 0 --delay-max 0
    "$PYTHON" tools/puzzle-scraper/bin/scrape_tapa.py --sizes 1 --delay-min 0 --delay-max 0
fi

echo ""
echo "health_check done"
exit "$health_status"
