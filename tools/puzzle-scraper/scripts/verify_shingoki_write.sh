#!/bin/zsh
# Fetch default Shingoki sizes and write to assets/data/Shingoki/.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO_ROOT"

LOG_DIR="$REPO_ROOT/tools/puzzle-scraper/logs"
LOG_FILE="$LOG_DIR/shingoki_verify.log"
mkdir -p "$LOG_DIR"

{
    echo "=== Shingoki verify run $(date -Iseconds) ==="
    python3 tools/puzzle-scraper/bin/scrape_shingoki.py --write --delay-min 1 --delay-max 2
    echo ""
    python3 - <<'PY'
import json
from pathlib import Path

path = Path("assets/data/Shingoki/Shingoki_dataset_000.json")
if not path.exists():
  raise SystemExit("missing Shingoki_dataset_000.json")
data = json.loads(path.read_text(encoding="utf-8"))
keys = sorted(data["data"].keys())
print(f"count={data['count']}")
print("case_ids:")
for key in keys:
    case = data["data"][key]
    first = case["problem"].splitlines()[0]
    print(f"  {key}  ({first})  {case['info']}")
PY
} 2>&1 | tee "$LOG_FILE"

echo "Log saved to $LOG_FILE"
