"""Entry point for the Shakashaka scraper."""

from __future__ import annotations

import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from sites.shakashaka import main

if __name__ == "__main__":
    raise SystemExit(main())
