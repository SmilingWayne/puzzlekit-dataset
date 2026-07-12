#!/usr/bin/env python3
from __future__ import annotations

import json
import sys

import puzzlekit


def json_safe_stats(data: dict) -> dict:
    safe = {}
    for key, value in data.items():
        if key == "solution_grid":
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
    return safe


def encode_solution_grid(matrix: list[list[str]]) -> str:
    rows = len(matrix)
    cols = len(matrix[0]) if rows else 0
    lines = [f"{rows} {cols}"]
    lines.extend(" ".join(str(token).strip() for token in row) for row in matrix)
    return "\n".join(lines)


def main() -> int:
    request = json.loads(sys.stdin.read())
    problem = request["problem"]
    time_limit_sec = float(request.get("timeLimitSec", 20))

    try:
        result = puzzlekit.solve(
            problem,
            "lits",
            solver_options={"time_limit_sec": time_limit_sec},
        )
        if not result.is_solved or result.sol_grid is None:
            status = result.solution_data.get("status", "unknown")
            print(json.dumps({"ok": False, "error": f"solve_failed:{status}"}))
            return 0

        print(
            json.dumps(
                {
                    "ok": True,
                    "solution": encode_solution_grid(result.sol_grid.matrix),
                    "stats": json_safe_stats(result.solution_data),
                }
            )
        )
        return 0
    except Exception as exc:  # noqa: BLE001 - bridge returns structured errors.
        print(json.dumps({"ok": False, "error": f"{type(exc).__name__}:{exc}"}))
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
