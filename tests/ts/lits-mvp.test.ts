import { describe, expect, it } from "vitest";

import {
  appendCases,
  buildCaseRecord,
  parseLitsProblemFromPzprFileData,
} from "../../tools/lits-mvp/core.js";

describe("LITS MVP pipeline helpers", () => {
  it("converts pzpr file data into dataset problem text", () => {
    const fileData = [
      "pzprv3",
      "lits",
      "2",
      "3",
      "2",
      "0 0 1 ",
      "0 1 1 ",
      ". . . ",
      ". . . ",
    ].join("\n");

    expect(parseLitsProblemFromPzprFileData(fileData)).toBe(
      "2 3\n0 0 1\n0 1 1",
    );
  });

  it("builds dataset records with empty source and original puzzlink URL", () => {
    const record = buildCaseRecord({
      problem: "2 3\n0 0 1\n0 1 1",
      solution: "2 3\nL L -\n- L L",
      puzzlinkUrl: "https://puzz.link/p?lits/3/2/example",
    });

    expect(record).toEqual({
      problem: "2 3\n0 0 1\n0 1 1",
      solution: "2 3\nL L -\n- L L",
      source: "",
      info: "",
      puzzlink_url: "https://puzz.link/p?lits/3/2/example",
    });
  });

  it("appends cases and recounts without dedupe filtering", () => {
    const dataset = {
      name: "LITS",
      count: 1,
      count_sol: 1,
      data: {
        existing: {
          problem: "1 1\n0",
          solution: "1 1\n-",
          source: "",
          info: "",
        },
      },
    };

    const next = appendCases(dataset, [
      {
        caseId: "lits0001",
        record: buildCaseRecord({
          problem: "2 3\n0 0 1\n0 1 1",
          solution: "2 3\nL L -\n- L L",
          puzzlinkUrl: "https://puzz.link/p?lits/3/2/example",
        }),
      },
    ]);

    expect(dataset.count).toBe(1);
    expect(next.count).toBe(2);
    expect(next.count_sol).toBe(2);
    expect(next.data.lits0001?.source).toBe("");
  });
});
