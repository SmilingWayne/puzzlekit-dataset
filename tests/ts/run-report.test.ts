import { describe, expect, it } from "vitest";

import {
  appendStageEvent,
  createCaseRun,
} from "../../src/pipeline/runReport.js";

describe("case run reports", () => {
  it("records immutable stage events for a pipeline case", () => {
    const initial = createCaseRun({
      caseId: "case-1",
      puzzleType: "masyu",
      sourceUrl: "https://puzz.link/p?masyu/2/2/a",
    });
    const parsed = appendStageEvent(initial, {
      stage: "parsed",
      status: "ok",
      message: "URL parsed by pzprjs adapter",
    });

    expect(initial.events).toEqual([]);
    expect(parsed).toMatchObject({
      caseId: "case-1",
      puzzleType: "masyu",
      sourceUrl: "https://puzz.link/p?masyu/2/2/a",
      finalStatus: "running",
      events: [
        {
          stage: "parsed",
          status: "ok",
          message: "URL parsed by pzprjs adapter",
        },
      ],
    });
    expect(parsed.events[0]?.at).toEqual(expect.any(String));
  });

  it("marks a case failed when a failed stage event is appended", () => {
    const initial = createCaseRun({
      caseId: "case-1",
      puzzleType: "masyu",
      sourceUrl: "https://puzz.link/p?masyu/2/2/a",
    });
    const failed = appendStageEvent(initial, {
      stage: "solved",
      status: "failed",
      message: "sidecar timeout",
    });

    expect(failed.finalStatus).toBe("failed");
  });
});
