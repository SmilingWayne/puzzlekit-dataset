export type PuzzleType = "lits" | "masyu" | "slitherlink" | string;

export type GridSize = {
  rows: number;
  cols: number;
};

export type DatasetPuzzle = {
  type: PuzzleType;
  size: GridSize;
  problemText: string;
  sourceUrl?: string;
  normalizedPuzzlinkUrl?: string;
  penpa?: string;
  raw?: unknown;
};

export type DatasetSolution = {
  status: "solved" | "unsolved" | "timeout" | "invalid" | "multiple" | "failed";
  solutionText?: string;
  penpaSolutions?: string[];
  reason?: string;
  diagnostics?: unknown;
};
