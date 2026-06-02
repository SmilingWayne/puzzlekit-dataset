from __future__ import annotations

from cleaners.contracts import canonical_region_rows, normalize_grid_text
from cleaners.core import clean_dataset_obj
from cleaners.registry import REGION_LAYOUTS, RIM_LAYOUTS, CleaningSpec


def _dataset(data: dict[str, dict]) -> dict:
    return {"name": "Test", "count": len(data), "count_sol": 0, "data": data}


def test_base_pipeline_normalizes_grid_text() -> None:
    spec = CleaningSpec("Test", "base")
    source = _dataset(
        {
            "a": {
                "problem": "2   2 \n  -   1 \n 2   -  ",
                "solution": "2 2\n -   x\nx   - ",
                "source": "",
                "info": "",
            }
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert result.modified == 1
    assert result.invalid_removed == 0
    assert cleaned["data"]["a"]["problem"] == "2 2\n- 1\n2 -"
    assert cleaned["data"]["a"]["solution"] == "2 2\n- x\nx -"


def test_base_pipeline_dedupes_exact_normalized_problem() -> None:
    spec = CleaningSpec("Test", "base")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n- 1\n2 -",
                "solution": "",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2\n -   1 \n 2   - ",
                "solution": "",
                "source": "",
                "info": "",
            },
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert list(cleaned["data"]) == ["first"]
    assert result.duplicate_removed == 1
    assert result.dedupe_groups[0].kept_id == "first"
    assert result.dedupe_groups[0].removed_ids == ["second"]


def test_region_clues_regions_dedupes_with_header_and_bijection() -> None:
    spec = CleaningSpec("Aqre", "region")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n- -\n- -\na a\nb b",
                "solution": "2 2\n- x\nx -",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2\n- -\n- -\nx x\ny y",
                "solution": "2 2\n- x\nx -",
                "source": "",
                "info": "",
            },
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert list(cleaned["data"]) == ["first"]
    assert result.duplicate_removed == 1


def test_region_clues_regions_does_not_dedupe_different_headers() -> None:
    spec = CleaningSpec("Aqre", "region")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n- -\n- -\na a\nb b",
                "solution": "",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2 1\n- -\n- -\na a\nb b",
                "solution": "",
                "source": "",
                "info": "",
            },
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert len(cleaned["data"]) == 2
    assert result.duplicate_removed == 0


def test_region_hole_token_participates_in_canonical_key() -> None:
    left = canonical_region_rows(["a @ b", "a @ b"])
    right = canonical_region_rows(["x @ y", "x @ y"])
    different_holes = canonical_region_rows(["x y @", "x y @"])

    assert left == right
    assert left != different_holes


def test_region_partition_only_dedupes_region_bijection() -> None:
    spec = CleaningSpec("LITS", "region")
    assert REGION_LAYOUTS["LITS"].body == "regions"
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n1 1\n2 2",
                "solution": "",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2\na a\nb b",
                "solution": "",
                "source": "",
                "info": "",
            },
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert list(cleaned["data"]) == ["first"]
    assert result.duplicate_removed == 1


def test_region_partition_only_does_not_dedupe_different_headers() -> None:
    spec = CleaningSpec("Starbattle", "region")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n1 1\n2 2",
                "solution": "",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2 1\n1 1\n2 2",
                "solution": "",
                "source": "",
                "info": "",
            },
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert len(cleaned["data"]) == 2
    assert result.duplicate_removed == 0


def test_region_partition_hash_hole_token_participates_in_canonical_key() -> None:
    holes = frozenset({"@", "#"})
    left = canonical_region_rows(["a # b", "a # b"], hole_tokens=holes)
    right = canonical_region_rows(["x # y", "x # y"], hole_tokens=holes)
    different_holes = canonical_region_rows(["x y #", "x y #"], hole_tokens=holes)

    assert left == right
    assert left != different_holes


def test_rim_2_none_dedupes_same_edges() -> None:
    spec = CleaningSpec("Gappy", "rim")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n1 2\n3 4",
                "solution": "2 2\n- x\nx -",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2\n1 2\n3 4",
                "solution": "2 2\nx -\n- x",
                "source": "",
                "info": "",
            },
        }
    )
    cleaned, result = clean_dataset_obj(source, spec)
    assert result.duplicate_removed == 1
    assert list(cleaned["data"]) == ["first"]


def test_rim_2_clues_dedupes_only_when_clues_match() -> None:
    spec = CleaningSpec("Pipeline", "rim")
    source = _dataset(
        {
            "first": {
                "problem": "2 2\n1 2\n3 4\n- 1\n2 -",
                "solution": "2 2\n- x\nx -",
                "source": "",
                "info": "",
            },
            "second": {
                "problem": "2 2\n1 2\n3 4\nx -\n- x",
                "solution": "2 2\n- x\nx -",
                "source": "",
                "info": "",
            },
        }
    )
    cleaned, result = clean_dataset_obj(source, spec)
    assert result.duplicate_removed == 0
    assert len(cleaned["data"]) == 2


def test_rim_clues_regions_requires_both_parts() -> None:
    layout = RIM_LAYOUTS["OneToX"]
    spec = CleaningSpec("OneToX", "rim")
    source = _dataset(
        {
            "a": {
                "problem": (
                    "2 2\n1 2\n3 4\n- -\n- -\n1 1\n2 2"
                ),
                "solution": "2 2\n1 2\n3 4",
                "source": "",
                "info": "",
            },
            "b": {
                "problem": (
                    "2 2\n1 2\n3 4\n- -\n- -\n1 2\n2 1"
                ),
                "solution": "2 2\n1 2\n3 4",
                "source": "",
                "info": "",
            },
        }
    )
    cleaned, result = clean_dataset_obj(source, spec)
    assert result.duplicate_removed == 0
    assert len(cleaned["data"]) == 2
    assert layout.body == "clues_regions"


def test_empty_solution_is_kept_without_invalid_removal() -> None:
    spec = CleaningSpec("Test", "base")
    source = _dataset(
        {
            "empty": {
                "problem": "2 2\n- -\n- -",
                "solution": "",
                "source": "",
                "info": "",
            }
        }
    )

    cleaned, result = clean_dataset_obj(source, spec)

    assert result.invalid_removed == 0
    assert cleaned["count"] == 1
    assert cleaned["count_sol"] == 0


def test_normalization_preserves_blank_lines_for_validation() -> None:
    normalized = normalize_grid_text("2 2\n- -\n\n- -")

    assert normalized.text == "2 2\n- -\n\n- -"


def test_normalization_strips_leading_and_trailing_blank_lines() -> None:
    normalized = normalize_grid_text("2 2\n- -\n- -\n")

    assert normalized.text == "2 2\n- -\n- -"
    assert normalized.changed is True


def test_trailing_newline_solution_passes_grid_validation() -> None:
    from cleaners.contracts import validate_grid_text

    raw = "2 2\n- x\nx -\n"
    normalized = normalize_grid_text(raw)

    assert validate_grid_text(normalized.text).valid
