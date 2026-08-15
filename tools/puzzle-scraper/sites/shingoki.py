from __future__ import annotations

import re
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent
if str(TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(TOOLS_DIR))

from lib.runner import ScraperSpec, build_arg_parser, run_scraper
from lib.store import build_problem

SITE = "https://www.puzzle-shingoki.com"
REPO_ROOT = TOOLS_DIR.parent.parent
OUTPUT_DIR = REPO_ROOT / "assets" / "scraped" / "shingoki"
DEFAULT_SIZES = list(range(0, 20))

_RE_TASK = re.compile(r"var task = '([^']+)'")
_RE_IDENT = re.compile(r"ident: '([^']+)'")
_RE_DIMS = re.compile(r"puzzleWidth: (\d+), puzzleHeight: (\d+)")
_RE_HASHED = re.compile(r"hashedSolution: '([^']+)'")
_RE_PUZZLE_ID = re.compile(r'id="puzzleID">([^<]+)<')
_RE_TITLE = re.compile(r'class="puzzleInfo">\s*(.*?)\s*(?:Puzzle ID:|<span)', re.S)
_RE_PLSIZE = re.compile(r"Game\.plSize = (\d+);")
_RE_LOADED_ID = re.compile(r"var loadedId = (\d+);")
_RE_PUZZLE_DATE = re.compile(r'<select name="date"><option[^>]*value="(\d{4}-\d{2}-\d{2})"[^>]*selected')

SPEC = ScraperSpec(
    name="Shingoki",
    site=SITE,
    file_prefix="shingoki",
    default_sizes=DEFAULT_SIZES,
    output_dir=OUTPUT_DIR,
    description="Scrape puzzle-shingoki.com puzzles into a rolling JSON store.",
)


_RE_TITLE_DATE = re.compile(r"\((\d{4}-\d{2}-\d{2})\)")


def extract(html: str) -> dict:
    task_match = _RE_TASK.search(html)
    if task_match is None:
        raise ValueError("no var task found in page")
    dims = _RE_DIMS.search(html)
    plsize = _RE_PLSIZE.search(html)
    pid = _RE_PUZZLE_ID.search(html)
    title = _RE_TITLE.search(html)
    date_match = _RE_PUZZLE_DATE.search(html)
    ident_match = _RE_IDENT.search(html)
    hashed_match = _RE_HASHED.search(html)
    loaded_match = _RE_LOADED_ID.search(html)
    puzzle_id = re.sub(r"\D", "", pid.group(1)) if pid else None
    if puzzle_id in ("", "0"):
        puzzle_id = None
    title_text = re.sub(r"\s+", " ", title.group(1)).rstrip("-").strip() if title else None
    puzzle_date = date_match.group(1) if date_match else None
    if not puzzle_date and title_text:
        title_date = _RE_TITLE_DATE.search(title_text)
        if title_date:
            puzzle_date = title_date.group(1)
    return {
        "task": task_match.group(1),
        "ident": ident_match.group(1) if ident_match else None,
        "dims": (int(dims.group(1)), int(dims.group(2))) if dims else None,
        "hashed_solution": hashed_match.group(1) if hashed_match else None,
        "puzzle_id": puzzle_id,
        "loaded_id": loaded_match.group(1) if loaded_match else None,
        "title": title_text,
        "pl_size": int(plsize.group(1)) if plsize else None,
        "puzzle_date": puzzle_date,
    }


def grid_dims(puzzle_dims: tuple[int, int]) -> tuple[int, int]:
    """Site puzzleWidth/Height count unit squares; task encodes their corner dots."""
    w, h = puzzle_dims
    return (w + 1, h + 1)


def decode_task(task: str) -> list[str]:
    """Decode Shingoki task strings: B6/W2 pearls and a-z gap runs."""
    cells: list[str] = []
    i = 0
    while i < len(task):
        ch = task[i]
        if ch in "BW":
            j = i + 1
            while j < len(task) and task[j].isdigit():
                j += 1
            value = task[i + 1 : j]
            if not value:
                raise ValueError(f"missing pearl value after {ch!r} at position {i}")
            cells.append(("b" if ch == "B" else "w") + value)
            i = j
        elif "a" <= ch <= "z":
            cells.extend(["-"] * (ord(ch) - ord("a") + 1))
            i += 1
        else:
            raise ValueError(f"unexpected character {ch!r} at position {i}")
    return cells


def make_case_id(raw: dict, size: int) -> str | None:
    loaded_id = raw.get("loaded_id")
    if loaded_id in (None, "", "0"):
        loaded_id = None
    puzzle_id = raw.get("puzzle_id")
    if puzzle_id in (None, "", "0"):
        puzzle_id = None
    cid = puzzle_id or raw.get("puzzle_date") or loaded_id
    if not cid:
        return None
    pl_size = raw["pl_size"] if raw["pl_size"] is not None else size
    return f"size{pl_size}_{cid}"


def build_case(raw: dict, url: str, fetched_at: str) -> dict:
    cells = decode_task(raw["task"])
    dims = raw["dims"]
    if dims is None:
        raise ValueError("missing puzzle dimensions")
    grid = grid_dims(dims)
    if len(cells) != grid[0] * grid[1]:
        raise ValueError(f"decoded {len(cells)} cells, expected {grid[0]}x{grid[1]}")
    info_bits = [raw["title"] or raw["ident"] or "Shingoki"]
    if raw["puzzle_date"]:
        info_bits.append(f"({raw['puzzle_date']})")
    return {
        "problem": build_problem(grid, cells),
        "solution": "",
        "source": url,
        "info": " ".join(info_bits),
        "fetched_at": fetched_at,
    }


def main(argv: list[str] | None = None) -> int:
    parser = build_arg_parser(SPEC)
    args = parser.parse_args(argv)
    return run_scraper(
        SPEC,
        sizes=args.sizes,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
        write=args.write,
        out_dir=args.out,
        summary=args.summary,
        extract=extract,
        build_case=build_case,
        case_id=make_case_id,
    )


if __name__ == "__main__":
    raise SystemExit(main())
