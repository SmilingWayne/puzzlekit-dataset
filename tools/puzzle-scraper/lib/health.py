"""Validate rolling scraped stores without relying on jsonl logs."""

from __future__ import annotations

import json
from pathlib import Path

STORES: tuple[tuple[str, str], ...] = (
    ("masyu", "masyu"),
    ("shingoki", "shingoki"),
    ("shakashaka", "shakashaka"),
    ("hashi", "hashi"),
    ("tapa", "tapa"),
)


def store_dir(repo_root: Path, kind: str) -> Path:
    return repo_root / "assets" / "scraped" / kind


def store_files(repo_root: Path, kind: str, prefix: str) -> list[Path]:
    directory = store_dir(repo_root, kind)
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"{prefix}_*.json"))


def fetched_date(case: dict) -> str | None:
    raw = case.get("fetched_at") or ""
    if len(raw) < 10:
        return None
    return raw[:10]


def validate_store(data: dict) -> list[str]:
    errors: list[str] = []
    cases = data.get("data")
    if not isinstance(cases, dict):
        return ["missing data object"]
    if data.get("count") != len(cases):
        errors.append(f"count {data.get('count')!r} != len(data) {len(cases)}")
    sol = sum(1 for case in cases.values() if case.get("solution"))
    if data.get("count_sol") not in (None, sol):
        errors.append(f"count_sol {data.get('count_sol')!r} != {sol}")
    for cid, case in cases.items():
        if not isinstance(case, dict):
            errors.append(f"{cid}: case is not an object")
            continue
        problem = case.get("problem") or ""
        if not problem:
            errors.append(f"{cid}: empty problem")
            continue
        header = problem.splitlines()[0]
        parts = header.split()
        if len(parts) != 2 or not all(part.isdigit() for part in parts):
            errors.append(f"{cid}: bad problem header {header!r}")
        if not case.get("source"):
            errors.append(f"{cid}: missing source")
    return errors


def summarize_kind(repo_root: Path, kind: str, prefix: str, today: str | None = None) -> dict:
    files = store_files(repo_root, kind, prefix)
    errors: list[str] = []
    total = 0
    fetched_today = 0
    file_rows: list[dict] = []
    if not files:
        errors.append("no store files")
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{path.name}: {exc}")
            continue
        case_errors = [f"{path.name}: {item}" for item in validate_store(data)]
        errors.extend(case_errors)
        cases = data.get("data") if isinstance(data.get("data"), dict) else {}
        total += len(cases)
        if today:
            fetched_today += sum(1 for case in cases.values() if fetched_date(case) == today)
        file_rows.append({"file": path.name, "count": len(cases)})
    return {
        "kind": kind,
        "files": file_rows,
        "total_cases": total,
        "fetched_today": fetched_today,
        "ok": not errors,
        "errors": errors,
    }


def summarize_all(repo_root: Path, today: str | None = None) -> list[dict]:
    return [summarize_kind(repo_root, kind, prefix, today=today) for kind, prefix in STORES]


def format_report(rows: list[dict], today: str | None = None) -> str:
    lines: list[str] = []
    if today:
        lines.append(f"today (UTC date prefix): {today}")
    for row in rows:
        names = [item["file"] for item in row["files"]]
        lines.append(
            f"{row['kind']}: {row['total_cases']} cases in {len(row['files'])} file(s)"
            + (f" — {names}" if names else "")
            + (f"; fetched_today={row['fetched_today']}" if today else "")
        )
        if not row["ok"]:
            for error in row["errors"]:
                lines.append(f"  ERROR {error}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    import argparse
    from datetime import datetime, timezone

    parser = argparse.ArgumentParser(description="Validate assets/scraped rolling JSON stores")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[3],
        help="Repository root",
    )
    parser.add_argument(
        "--today",
        default=datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        help="UTC date used for fetched_today counts",
    )
    args = parser.parse_args(argv)
    rows = summarize_all(args.root, today=args.today)
    print(format_report(rows, today=args.today))
    return 0 if all(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
