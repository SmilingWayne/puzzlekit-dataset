"""Internal contracts for the dataset cleaners package."""

from cleaners.contracts.dedupe import (
    canonical_region_rows,
    exact_problem_key,
    group_duplicate_keys,
)
from cleaners.contracts.ext import (
    ExtLayout,
    ext_problem_key,
    make_ext_dedupe_key,
    make_validate_ext,
    validate_ext_text,
)
from cleaners.contracts.layouts import (
    SizeHeader,
    ValidationResult,
    grid_rows,
    parse_size_header,
    region_parts,
    validate_grid_text,
    validate_region_text,
)
from cleaners.contracts.normalization import (
    NormalizeResult,
    normalize_grid_text,
    split_tokens,
)
from cleaners.contracts.region_layout import (
    RegionLayout,
    make_region_dedupe_key,
    make_validate_region,
    region_layout_problem_key,
    validate_region_layout_text,
)
from cleaners.contracts.rim import (
    RimLayout,
    make_rim_dedupe_key,
    make_validate_rim,
    rim_problem_key,
    validate_rim_text,
)
from cleaners.contracts.special import (
    validate_consecutive_text,
    validate_nonogram_text,
    validate_thermometer_text,
)
from cleaners.contracts.results import (
    CaseError,
    DedupeGroup,
    PuzzleCleaningResult,
)

__all__ = [
    "CaseError",
    "DedupeGroup",
    "NormalizeResult",
    "PuzzleCleaningResult",
    "SizeHeader",
    "ValidationResult",
    "canonical_region_rows",
    "exact_problem_key",
    "ext_problem_key",
    "grid_rows",
    "group_duplicate_keys",
    "normalize_grid_text",
    "parse_size_header",
    "region_parts",
    "RimLayout",
    "RegionLayout",
    "ExtLayout",
    "region_layout_problem_key",
    "rim_problem_key",
    "make_ext_dedupe_key",
    "make_region_dedupe_key",
    "make_validate_ext",
    "make_validate_region",
    "validate_ext_text",
    "validate_region_layout_text",
    "split_tokens",
    "validate_rim_text",
    "make_rim_dedupe_key",
    "make_validate_rim",
    "validate_grid_text",
    "validate_nonogram_text",
    "validate_region_text",
    "validate_thermometer_text",
    "validate_consecutive_text",
]
