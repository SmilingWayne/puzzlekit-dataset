"""Decode, solve, and encode a single catalog entry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import puzzlekit
from puzzlekit.formats.dataset_text import encode_problem, encode_solution

from ingest.catalog import CatalogEntry


@dataclass
class IngestResult:
    entry: CatalogEntry
    ok: bool
    case_id: str = ""
    case: dict[str, Any] | None = None
    error: str = ""
    skip_reason: str = ""


def _normalize_problem_key(problem: str) -> str:
    lines = [line.strip() for line in problem.replace("\r\n", "\n").replace("\r", "\n").split("\n")]
    return "\n".join(" ".join(line.split()) if line else "" for line in lines if line != "" or len(lines) <= 1).strip()


def process_entry(
    entry: CatalogEntry,
    *,
    puzzlekit_type: str,
    time_limit_sec: float = 60.0,
) -> IngestResult:
    try:
        inst = puzzlekit.decode(entry.puzz_link_url)
        problem = encode_problem(inst)
        result = puzzlekit.solve(
            problem,
            puzzlekit_type,
            solver_options={"time_limit_sec": time_limit_sec},
        )
        if not result.is_solved or result.sol_grid is None:
            status = result.solution_data.get("status", "Unknown")
            return IngestResult(entry=entry, ok=False, error=f"solve_failed:{status}")

        solution = encode_solution(
            puzzlekit_type,
            result.sol_grid,
            inst.rows,
            inst.cols,
        )
        case_id = entry.name or f"pz_{puzzlekit_type}_{abs(hash(entry.puzz_link_url)) & 0xFFFFFFFF:08x}"
        case = {
            "problem": problem,
            "solution": solution,
            "source": "",
            "info": "",
            "puzzlink_url": entry.puzz_link_url,
        }
        return IngestResult(entry=entry, ok=True, case_id=case_id, case=case)
    except Exception as exc:  # noqa: BLE001
        return IngestResult(entry=entry, ok=False, error=f"{type(exc).__name__}:{exc}")


def build_dedupe_index(dataset: dict) -> tuple[set[str], set[str]]:
  """Return (puzzlink_urls, normalized_problem_keys) from an existing dataset."""
  urls: set[str] = set()
  problems: set[str] = set()
  for case in dataset.get("data", {}).values():
    url = str(case.get("puzzlink_url", "")).strip()
    if url:
      urls.add(url)
    source = str(case.get("source", "")).strip()
    if "puzz.link/p?" in source:
      urls.add(source)
    problem = str(case.get("problem", "")).strip()
    if problem:
      problems.add(_normalize_problem_key(problem))
  return urls, problems
