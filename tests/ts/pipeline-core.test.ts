import { describe, expect, it } from "vitest";

import {
  mergePipelineResults,
  normalizeProblemKey,
} from "../../src/pipeline/merge.js";
import {
  normalizeNoqxResponse,
  toNoqxSolveRequest,
} from "../../src/pipeline/noqx.js";

describe("normalizeProblemKey", () => {
  it("normalizes line endings, outer whitespace, and repeated token spacing", () => {
    const problem = "  2  3\r\n  -   1  - \n\n";

    expect(normalizeProblemKey(problem)).toBe("2 3\n- 1 -");
  });
});

describe("mergePipelineResults", () => {
  it("adds solved cases without mutating existing dataset records", () => {
    const dataset = {
      name: "Masyu",
      count: 1,
      count_sol: 1,
      data: {
        existing: {
          problem: "2 2\n- w\n- -",
          solution: "2 2\nse sw\nne nw",
          source: "",
          info: "",
          puzzlink_url: "https://puzz.link/p?masyu/2/2/a",
        },
      },
    };

    const merged = mergePipelineResults(dataset, [
      {
        status: "solved",
        caseId: "new_case",
        caseRecord: {
          problem: "2 2\n- b\n- -",
          solution: "2 2\nse sw\nne nw",
          source: "",
          info: "",
          puzzlink_url: "https://puzz.link/p?masyu/2/2/b",
        },
      },
    ]);

    expect(dataset.count).toBe(1);
    expect(Object.keys(dataset.data)).toEqual(["existing"]);
    expect(merged.dataset.count).toBe(2);
    expect(merged.dataset.count_sol).toBe(2);
    expect(merged.report.addedIds).toEqual(["new_case"]);
    expect(merged.report.added).toBe(1);
  });

  it("reports URL duplicates and problem duplicates before adding records", () => {
    const dataset = {
      name: "Masyu",
      count: 1,
      count_sol: 1,
      data: {
        existing: {
          problem: "2 2\n- w\n- -",
          solution: "2 2\nse sw\nne nw",
          source: "",
          info: "",
          puzzlink_url: "https://puzz.link/p?masyu/2/2/a",
        },
      },
    };

    const merged = mergePipelineResults(dataset, [
      {
        status: "solved",
        caseId: "url_dup",
        caseRecord: {
          problem: "2 2\n- b\n- -",
          solution: "2 2\nse sw\nne nw",
          source: "",
          info: "",
          puzzlink_url: "https://puzz.link/p?masyu/2/2/a",
        },
      },
      {
        status: "solved",
        caseId: "problem_dup",
        caseRecord: {
          problem: " 2   2\n -   w\n-   - ",
          solution: "2 2\nse sw\nne nw",
          source: "",
          info: "",
          puzzlink_url: "https://puzz.link/p?masyu/2/2/c",
        },
      },
    ]);

    expect(merged.dataset.count).toBe(1);
    expect(merged.report.skippedUrlDup).toBe(1);
    expect(merged.report.skippedProblemDup).toBe(1);
  });
});

describe("noqx protocol", () => {
  it("builds stable solve requests for the sidecar boundary", () => {
    const request = toNoqxSolveRequest({
      requestId: "case-1",
      puzzleType: "masyu",
      penpa: "m=edit&p=abc",
      timeoutMs: 30_000,
      maxSolutions: 2,
    });

    expect(request).toEqual({
      requestId: "case-1",
      puzzleType: "masyu",
      penpa: "m=edit&p=abc",
      options: {
        timeoutMs: 30_000,
        maxSolutions: 2,
      },
    });
  });

  it("normalizes noqx url arrays into solution statuses", () => {
    expect(normalizeNoqxResponse({ url: ["solution"] })).toEqual({
      status: "solved",
      penpaSolutions: ["solution"],
    });
    expect(normalizeNoqxResponse({ url: [] })).toEqual({
      status: "unsolved",
      penpaSolutions: [],
      reason: "no_solution",
    });
    expect(normalizeNoqxResponse({ url: ["a", "b"] })).toEqual({
      status: "multiple",
      penpaSolutions: ["a", "b"],
      reason: "multiple_solutions",
    });
  });
});
