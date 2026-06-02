"""Dataset cleaning pipeline core."""

from __future__ import annotations

import copy
from collections.abc import Hashable

from cleaners.contracts import (
    CaseError,
    DedupeGroup,
    PuzzleCleaningResult,
    group_duplicate_keys,
    normalize_grid_text,
)
from cleaners.registry import CleaningSpec, get_pipeline_config


def _count_sol(data: dict[str, dict]) -> int:
    return sum(1 for case in data.values() if str(case.get("solution", "")).strip())


def clean_dataset_obj(
    source: dict,
    spec: CleaningSpec,
    *,
    wrote: bool = False,
) -> tuple[dict, PuzzleCleaningResult]:
    """Run the cleaning pipeline for one dataset object (in memory)."""

    config = get_pipeline_config(spec.pipeline, puzzle_name=spec.puzzle_name)
    if config is None:
        raise ValueError(f"pipeline {spec.pipeline!r} cannot clean datasets")

    validate_problem = config.validate_problem
    validate_solution = config.validate_solution
    dedupe_key_fn = config.dedupe_key
    input_total = len(source.get("data", {}))
    cleaned = copy.deepcopy(source)
    data: dict[str, dict] = cleaned.setdefault("data", {})

    survivors: list[tuple[str, dict, bool]] = []
    errors: list[CaseError] = []

    for case_id, case in data.items():
        case_copy = copy.deepcopy(case)
        problem_norm = normalize_grid_text(str(case_copy.get("problem", "")))
        solution_raw = str(case_copy.get("solution", ""))
        solution_norm = (
            normalize_grid_text(solution_raw) if solution_raw.strip() else None
        )

        case_changed = problem_norm.changed
        case_copy["problem"] = problem_norm.text
        if solution_norm is not None:
            case_copy["solution"] = solution_norm.text
            case_changed = case_changed or solution_norm.changed

        problem_check = validate_problem(case_copy["problem"])
        if not problem_check.valid:
            errors.append(
                CaseError(case_id, problem_check.reason or "invalid problem")
            )
            continue

        if solution_norm is not None:
            solution_check = validate_solution(case_copy["solution"])
            if not solution_check.valid:
                errors.append(
                    CaseError(
                        case_id,
                        solution_check.reason or "invalid solution",
                    )
                )
                continue

        survivors.append((case_id, case_copy, case_changed))

    dedupe_items: list[tuple[str, Hashable]] = [
        (case_id, dedupe_key_fn(case_copy["problem"]))
        for case_id, case_copy, _ in survivors
    ]
    duplicate_groups = group_duplicate_keys(dedupe_items)
    removed_ids: set[str] = set()
    dedupe_groups: list[DedupeGroup] = []
    for kept_id, dup_removed in duplicate_groups.items():
        dedupe_groups.append(DedupeGroup(kept_id=kept_id, removed_ids=dup_removed))
        removed_ids.update(dup_removed)

    output_data: dict[str, dict] = {}
    modified = 0
    for case_id, case_copy, case_changed in survivors:
        if case_id in removed_ids:
            continue
        output_data[case_id] = case_copy
        if case_changed:
            modified += 1

    cleaned["data"] = output_data
    cleaned["count"] = len(output_data)
    cleaned["count_sol"] = _count_sol(output_data)
    if "name" not in cleaned or not cleaned["name"]:
        cleaned["name"] = spec.puzzle_name

    duplicate_removed = len(removed_ids)
    result = PuzzleCleaningResult(
        puzzle=spec.puzzle_name,
        pipeline=spec.pipeline,
        input_total=input_total,
        modified=modified,
        invalid_removed=len(errors),
        duplicate_removed=duplicate_removed,
        output_total=len(output_data),
        count_sol=cleaned["count_sol"],
        errors=errors,
        dedupe_groups=dedupe_groups,
        wrote=wrote,
    )
    return cleaned, result
