"""Result objects for dataset cleaning pipelines."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class CaseError:
    """A removed invalid case and the reason it failed validation."""

    case_id: str
    reason: str


@dataclass(frozen=True)
class DedupeGroup:
    """Duplicate cases removed in favor of the first kept case."""

    kept_id: str
    removed_ids: list[str]


@dataclass
class PuzzleCleaningResult:
    """Summary for one cleaned puzzle dataset."""

    puzzle: str
    pipeline: str
    input_total: int
    modified: int
    invalid_removed: int
    duplicate_removed: int
    output_total: int
    count_sol: int
    errors: list[CaseError] = field(default_factory=list)
    dedupe_groups: list[DedupeGroup] = field(default_factory=list)
    wrote: bool = False

    def summary_line(self) -> str:
        """Compact one-line summary (for JSON reports and logs)."""

        mode = "write" if self.wrote else "dry-run"
        return (
            f"{self.puzzle} [{self.pipeline}, {mode}] "
            f"input={self.input_total} modified={self.modified} "
            f"invalid_removed={self.invalid_removed} "
            f"duplicate_removed={self.duplicate_removed} "
            f"output={self.output_total} count_sol={self.count_sol}"
        )
