export type PipelineStage =
  | "loaded"
  | "parsed"
  | "normalized"
  | "converted"
  | "solved"
  | "verified"
  | "written";

export type StageStatus = "ok" | "skipped" | "failed";

export type StageEvent = {
  stage: PipelineStage;
  status: StageStatus;
  message: string;
  at: string;
  diagnostics?: unknown;
};

export type StageEventInput = Omit<StageEvent, "at"> & {
  at?: string;
};

export type CaseRun = {
  caseId: string;
  puzzleType: string;
  sourceUrl?: string;
  finalStatus: "running" | "completed" | "skipped" | "failed";
  events: StageEvent[];
};

export function createCaseRun(input: {
  caseId: string;
  puzzleType: string;
  sourceUrl?: string;
}): CaseRun {
  return {
    caseId: input.caseId,
    puzzleType: input.puzzleType,
    sourceUrl: input.sourceUrl,
    finalStatus: "running",
    events: [],
  };
}

export function appendStageEvent(
  run: CaseRun,
  event: StageEventInput,
): CaseRun {
  const stageEvent: StageEvent = {
    ...event,
    at: event.at ?? new Date().toISOString(),
  };

  return {
    ...run,
    finalStatus:
      event.status === "failed"
        ? "failed"
        : event.status === "skipped"
          ? "skipped"
          : run.finalStatus,
    events: [...run.events, stageEvent],
  };
}
