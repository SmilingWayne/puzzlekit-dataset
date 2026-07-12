import { describe, expect, it } from "vitest";

import {
  createSolverBackendRegistry,
  type SolverBackend,
} from "../../src/pipeline/solverBackend.js";

describe("solver backend registry", () => {
  it("resolves a configured default backend without coupling callers to noqx", async () => {
    const backend: SolverBackend = {
      id: "fake-solver",
      solve: async () => ({
        status: "solved",
        penpaSolutions: ["solution"],
      }),
    };
    const registry = createSolverBackendRegistry({
      defaultBackendId: "fake-solver",
      backends: [backend],
    });

    expect(registry.defaultBackend().id).toBe("fake-solver");
    await expect(
      registry.defaultBackend().solve({
        requestId: "case-1",
        puzzleType: "masyu",
        penpa: "m=edit&p=abc",
        options: {
          timeoutMs: 30_000,
          maxSolutions: 2,
        },
      }),
    ).resolves.toEqual({
      status: "solved",
      penpaSolutions: ["solution"],
    });
  });

  it("fails early when the configured backend is missing", () => {
    const registry = createSolverBackendRegistry({
      defaultBackendId: "missing",
      backends: [],
    });

    expect(() => registry.defaultBackend()).toThrow(
      "Solver backend 'missing' is not registered",
    );
  });
});
