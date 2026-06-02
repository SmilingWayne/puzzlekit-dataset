"""Puzzle name to cleaning pipeline registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from cleaners.contracts.dedupe import exact_problem_key
from cleaners.contracts.ext import (
    ExtLayout,
    make_ext_dedupe_key,
    make_validate_ext,
)
from cleaners.contracts.layouts import (
    ValidationResult,
    validate_grid_text,
)
from cleaners.contracts.special import (
    validate_consecutive_text,
    validate_nonogram_text,
    validate_thermometer_text,
)
from cleaners.contracts.region_layout import (
    REGION_PARTITION_HOLE_TOKENS,
    RegionLayout,
    make_region_dedupe_key,
    make_validate_region,
)
from cleaners.contracts.rim import (
    RimLayout,
    make_rim_dedupe_key,
    make_validate_rim,
)


@dataclass(frozen=True)
class CleaningSpec:
    puzzle_name: str
    pipeline: str  # "base" | "region" | "rim" | "ext" | "s1" | "s2" | "s3" | "none"


PipelineName = str
ValidateFn = Callable[[str], ValidationResult]
DedupeKeyFn = Callable[[str], object]


@dataclass(frozen=True)
class PipelineConfig:
    validate_problem: ValidateFn
    validate_solution: ValidateFn
    dedupe_key: DedupeKeyFn


_PIPELINE_CONFIG: dict[PipelineName, PipelineConfig] = {
    "base": PipelineConfig(
        validate_problem=validate_grid_text,
        validate_solution=validate_grid_text,
        dedupe_key=exact_problem_key,
    ),
    "s1": PipelineConfig(
        validate_problem=validate_nonogram_text,
        validate_solution=validate_grid_text,
        dedupe_key=exact_problem_key,
    ),
    "s2": PipelineConfig(
        validate_problem=validate_thermometer_text,
        validate_solution=validate_grid_text,
        dedupe_key=exact_problem_key,
    ),
    "s3": PipelineConfig(
        validate_problem=validate_consecutive_text,
        validate_solution=validate_grid_text,
        dedupe_key=exact_problem_key,
    ),
}


# Region layouts — 1+m (regions) or 1+2m (clues + regions); see README § Cleaning.
_REGION_CLUES_PUZZLES: tuple[str, ...] = (
    "Aqre",
    "Chocona",
    "CocktailLamp",
    "Cojun",
    "CountryRoad",
    "Detour",
    "DiffNeighbors",
    "DotchiLoop",
    "Factors",
    "Hakoiri",
    "Hakyuu",
    "Hanare",
    "Heyawake",
    "JigsawSudoku",
    "Juosan",
    "KenKen",
    "KillerSudoku",
    "Makaro",
    "MoonSun",
    "Nanro",
    "Nondango",
    "PaintArea",
    "Patchwork",
    "Putteria",
    "RegionalYajilin",
    "Renban",
    "Shimaguni",
    "Suguru",
    "TerraX",
    "Tripletts",
    "Usoone",
)

_REGION_PARTITION_PUZZLES: tuple[str, ...] = (
    "DoubleBack",
    "EntryExit",
    "LITS",
    "Norinori",
    "Starbattle",
)

REGION_LAYOUTS: dict[str, RegionLayout] = {
    **{name: RegionLayout(body="clues_regions") for name in _REGION_CLUES_PUZZLES},
    **{
        name: RegionLayout(
            body="regions",
            hole_tokens=REGION_PARTITION_HOLE_TOKENS,
        )
        for name in _REGION_PARTITION_PUZZLES
    },
}

# Rim (edge-clue) layouts — see README § Formats / Cleaning.
RIM_LAYOUTS: dict[str, RimLayout] = {
    "ABCEndView": RimLayout(edges=4, body="none", optional_body="clues"),
    "Battleship": RimLayout(edges=2, body="clues", optional_body="none"),
    "DigitalBattleship": RimLayout(edges=2, body="clues"),
    "DoppelBlock": RimLayout(edges=2, body="none"),
    "Gappy": RimLayout(edges=2, body="none"),
    "Kakurasu": RimLayout(edges=2, body="none"),
    "MarginSudoku": RimLayout(edges=4, body="none"),
    "Magnetic": RimLayout(edges=4, body="clues_regions", hole_tokens=frozenset({"@"})),
    "NumberCross": RimLayout(edges=2, body="clues"),
    "OneToX": RimLayout(edges=2, body="clues_regions"),
    "Pills": RimLayout(edges=2, body="clues"),
    "Pipeline": RimLayout(edges=2, body="clues"),
    "Skyscraper": RimLayout(edges=4, body="none", optional_body="clues"),
    "SkyscraperSudoku": RimLayout(edges=4, body="clues"),
    "Snake": RimLayout(edges=2, body="clues"),
    "Sternenhimmel": RimLayout(edges=2, body="clues"),
    "Stitches": RimLayout(edges=2, body="regions"),
    "Tent": RimLayout(edges=2, body="clues"),
    "TilePaint": RimLayout(edges=2, body="regions"),
}

# Extended layouts (non 1+m / region / rim forms).
EXT_LAYOUTS: dict[str, ExtLayout] = {
    "Creek": ExtLayout(kind="boundary"),
    "GokigenNaname": ExtLayout(kind="boundary"),
    "Mathrax": ExtLayout(kind="mathrax"),
}


def get_pipeline_config(
    pipeline: str,
    *,
    puzzle_name: str | None = None,
) -> PipelineConfig | None:
    if pipeline == "none":
        return None
    if pipeline == "region":
        if puzzle_name is None or puzzle_name not in REGION_LAYOUTS:
            return None
        layout = REGION_LAYOUTS[puzzle_name]
        return PipelineConfig(
            validate_problem=make_validate_region(layout),
            validate_solution=validate_grid_text,
            dedupe_key=make_region_dedupe_key(layout),
        )
    if pipeline == "rim":
        if puzzle_name is None or puzzle_name not in RIM_LAYOUTS:
            return None
        layout = RIM_LAYOUTS[puzzle_name]
        return PipelineConfig(
            validate_problem=make_validate_rim(layout),
            validate_solution=validate_grid_text,
            dedupe_key=make_rim_dedupe_key(layout),
        )
    if pipeline == "ext":
        if puzzle_name is None or puzzle_name not in EXT_LAYOUTS:
            return None
        layout = EXT_LAYOUTS[puzzle_name]
        return PipelineConfig(
            validate_problem=make_validate_ext(layout),
            validate_solution=validate_grid_text,
            dedupe_key=make_ext_dedupe_key(layout),
        )
    return _PIPELINE_CONFIG.get(pipeline)


# Layout 1.1 — grid-only, exact-string dedupe.
_BASE_PUZZLES: tuple[str, ...] = (
    "Akari",
    "Araf",
    "BalanceLoop",
    "Binairo",
    "Bosanowa",
    "Buraitoraito",
    "Burokku",
    "Bricks",
    "ButterflySudoku",
    "CanalView",
    "CastleWall",
    "Cave",
    "Clueless1Sudoku",
    "Clueless2Sudoku",
    "CurvingRoad",
    "Dominos",
    "Doors",
    "Eulero",
    "EvenOddSudoku",
    "Fillomino",
    "Fobidoshi",
    "Foseruzu",
    "Fuzuli",
    "Galaxies",
    "Gattai8Sudoku",
    "Geradeweg",
    "GrandTour",
    "Hashi",
    "Hidoku",
    "Hitori",
    "Kakkuru",
    "Kakuro",
    "Koburin",
    "Kuromasu",
    "Kuroshuto",
    "Kurotto",
    "Linesweeper",
    "Masyu",
    "Mejilink",
    "MidLoop",
    "Minesweeper",
    "Mosaic",
    "Nanbaboru",
    "Munraito",
    "Nawabari",
    "NumberLink",
    "NumberSnake",
    "Nurikabe",
    "Nurimisaki",
    "Pfeilzahlen",
    "Pipelink",
    "Rekuto",
    "SamuraiSudoku",
    "Shakashaka",
    "Shikaku",
    "Shingoki",
    "Shirokuro",
    "ShogunSudoku",
    "Shugaku",
    "SimpleLoop",
    "Slitherlink",
    "SoheiSudoku",
    "SquareO",
    "Str8t",
    "Sudoku",
    "Sukoro",
    "SumoSudoku",
    "Tatamibari",
    "TennerGrid",
    "Trinairo",
    "WindmillSudoku",
    "Yajikabe",
    "Yajilin",
    "YinYang",
    "Yonmasu",
)


def _build_registry() -> dict[str, CleaningSpec]:
    registry: dict[str, CleaningSpec] = {}
    for name in _BASE_PUZZLES:
        registry[name] = CleaningSpec(name, "base")
    for name in REGION_LAYOUTS:
        registry[name] = CleaningSpec(name, "region")
    for name in RIM_LAYOUTS:
        registry[name] = CleaningSpec(name, "rim")
    for name in EXT_LAYOUTS:
        registry[name] = CleaningSpec(name, "ext")
    registry["Nonogram"] = CleaningSpec("Nonogram", "s1")
    registry["Thermometer"] = CleaningSpec("Thermometer", "s2")
    registry["ConsecutiveSudoku"] = CleaningSpec("ConsecutiveSudoku", "s3")
    return registry


PUZZLE_REGISTRY: dict[str, CleaningSpec] = _build_registry()


def get_spec(puzzle_name: str) -> CleaningSpec:
    if puzzle_name in PUZZLE_REGISTRY:
        return PUZZLE_REGISTRY[puzzle_name]
    return CleaningSpec(puzzle_name, "none")


def get_pipeline_label(puzzle_name: str) -> str:
    """Return pipeline id for README tables, or '-' if unmanaged."""

    return PUZZLE_REGISTRY[puzzle_name].pipeline if puzzle_name in PUZZLE_REGISTRY else "-"


def list_managed_puzzles() -> list[str]:
    return sorted(PUZZLE_REGISTRY.keys())
