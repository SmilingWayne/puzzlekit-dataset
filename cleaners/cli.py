"""Command-line interface for dataset cleaners."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from cleaners.contracts import PuzzleCleaningResult
from cleaners.core import clean_dataset_obj
from cleaners.display import (
    format_report_payload,
    format_result,
    format_run_banner,
    format_run_totals,
    format_unchecked,
)
from cleaners.io import DATA_ROOT, REPO_ROOT, dataset_path, load_dataset, save_dataset
from cleaners.registry import get_spec, list_managed_puzzles
from cleaners.batch import write_batch_summary
from cleaners.report import changelog_markdown, load_latest_report, write_report


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="cleaners", description="Puzzle dataset cleaners")
    parser.add_argument(
        "--data-root",
        type=Path,
        default=DATA_ROOT,
        help="Root directory for assets/data (default: repo assets/data)",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run cleaning pipeline")
    run_parser.add_argument("--puzzle", action="append", dest="puzzles", metavar="NAME")
    run_parser.add_argument("--all", action="store_true", help="Run all registry puzzles")
    run_parser.add_argument(
        "--write",
        action="store_true",
        help="Write cleaned JSON to disk (default: dry-run only)",
    )
    run_parser.add_argument(
        "--changelog",
        action="store_true",
        help="Print changelog snippet for docs/CHANGELOG.md to stdout",
    )
    run_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print compact one-line summaries only",
    )
    run_parser.add_argument(
        "--summary",
        nargs="?",
        const=Path("cleaners/reports/dry_run_batch_latest"),
        type=Path,
        metavar="PATH",
        help="Write batch dry-run summary (.md + .json); default path if flag alone",
    )

    check_parser = subparsers.add_parser("check", help="Validate datasets without writing")
    check_parser.add_argument("--puzzle", action="append", dest="puzzles", metavar="NAME")
    check_parser.add_argument("--all", action="store_true")
    check_parser.add_argument(
        "--quiet",
        action="store_true",
        help="Print compact one-line summaries only",
    )

    report_parser = subparsers.add_parser("report", help="Show cleaning reports")
    report_parser.add_argument("--latest", action="store_true", help="Show latest report")
    report_parser.add_argument(
        "--json",
        action="store_true",
        help="Print raw JSON (default: formatted text)",
    )

    return parser


def _resolve_puzzles(args: argparse.Namespace) -> list[str]:
    if getattr(args, "all", False):
        return list_managed_puzzles()
    puzzles = getattr(args, "puzzles", None) or []
    if not puzzles:
        raise SystemExit("Specify --puzzle NAME or --all")
    return puzzles


def _print_result(
    result: PuzzleCleaningResult,
    *,
    status: str,
    quiet: bool,
) -> None:
    if quiet:
        print(result.summary_line())
    else:
        print(format_result(result, status=status))
        print()


def _run_one(
    puzzle_name: str,
    *,
    data_root: Path,
    write: bool,
    print_changelog: bool,
    check_only: bool = False,
    quiet: bool = False,
) -> PuzzleCleaningResult:
    spec = get_spec(puzzle_name)
    if spec.pipeline == "none":
        if quiet:
            print(f"skip {puzzle_name}: not in registry (pipeline=none)", file=sys.stderr)
        else:
            print(format_unchecked(puzzle_name))
            print()
        write_report(_unchecked_result(puzzle_name), status="unchecked")
        return _unchecked_result(puzzle_name)

    source = load_dataset(puzzle_name, data_root=data_root)
    cleaned, result = clean_dataset_obj(source, spec, wrote=write and not check_only)
    status = "check" if check_only else "ok"
    _print_result(result, status=status, quiet=quiet)

    if write and not check_only:
        path = save_dataset(puzzle_name, cleaned, data_root=data_root)
        if not quiet:
            print(f"  Wrote: {path.relative_to(REPO_ROOT)}")
            print()

    rel_path = dataset_path(puzzle_name, data_root=data_root).relative_to(REPO_ROOT)
    write_report(result, status=status)
    if print_changelog:
        print(changelog_markdown(result, dataset_path=str(rel_path)))
    return result


def _unchecked_result(puzzle_name: str) -> PuzzleCleaningResult:
    return PuzzleCleaningResult(
        puzzle=puzzle_name,
        pipeline="none",
        input_total=0,
        modified=0,
        invalid_removed=0,
        duplicate_removed=0,
        output_total=0,
        count_sol=0,
    )


def cmd_run(args: argparse.Namespace) -> int:
    write = bool(args.write)
    quiet = bool(args.quiet)
    puzzles = _resolve_puzzles(args)
    if not quiet and len(puzzles) > 0:
        print(format_run_banner(command="run", puzzles=puzzles, write=write), end="")

    exit_code = 0
    results: list[PuzzleCleaningResult] = []
    for puzzle_name in puzzles:
        try:
            result = _run_one(
                puzzle_name,
                data_root=args.data_root,
                write=write,
                print_changelog=args.changelog,
                quiet=quiet,
            )
            if result.pipeline != "none":
                results.append(result)
        except FileNotFoundError as exc:
            print(f"error {puzzle_name}: {exc}", file=sys.stderr)
            exit_code = 1
        except ValueError as exc:
            print(f"error {puzzle_name}: {exc}", file=sys.stderr)
            exit_code = 1

    if not quiet:
        print(format_run_totals(results), end="")

    if getattr(args, "summary", None) is not None and results:
        summary_path = write_batch_summary(results, args.summary).resolve()
        json_path = summary_path.with_suffix(".json")
        print(f"Summary: {summary_path.relative_to(REPO_ROOT.resolve())}", file=sys.stderr)
        print(f"         {json_path.relative_to(REPO_ROOT.resolve())}", file=sys.stderr)

    return exit_code


def cmd_check(args: argparse.Namespace) -> int:
    quiet = bool(args.quiet)
    puzzles = _resolve_puzzles(args)
    if not quiet and puzzles:
        print(format_run_banner(command="check", puzzles=puzzles, write=False), end="")

    exit_code = 0
    results: list[PuzzleCleaningResult] = []
    for puzzle_name in puzzles:
        spec = get_spec(puzzle_name)
        if spec.pipeline == "none":
            if quiet:
                print(f"skip {puzzle_name}: not in registry", file=sys.stderr)
            else:
                print(format_unchecked(puzzle_name))
                print()
            continue
        try:
            source = load_dataset(puzzle_name, data_root=args.data_root)
            _, result = clean_dataset_obj(source, spec, wrote=False)
            _print_result(result, status="check", quiet=quiet)
            write_report(result, status="check")
            results.append(result)
            if result.invalid_removed or result.duplicate_removed:
                exit_code = 1
        except FileNotFoundError as exc:
            print(f"error {puzzle_name}: {exc}", file=sys.stderr)
            exit_code = 1

    if not quiet:
        print(format_run_totals(results), end="")
    return exit_code


def cmd_report(args: argparse.Namespace) -> int:
    if args.latest:
        payload = load_latest_report()
        if payload is None:
            print("No reports found. Run `python -m cleaners run` first.", file=sys.stderr)
            return 1
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(format_report_payload(payload))
            print()
        return 0
    raise SystemExit("Use: cleaners report --latest")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        return cmd_run(args)
    if args.command == "check":
        return cmd_check(args)
    if args.command == "report":
        return cmd_report(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
