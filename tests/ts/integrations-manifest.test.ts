import { describe, expect, it } from "vitest";

import {
  loadIntegrationManifest,
  validateIntegrationManifest,
} from "../../tools/integrations/manifest.js";

describe("integration manifest", () => {
  it("records upstream tags and pinned commits for external tools", () => {
    const manifest = loadIntegrationManifest("integrations/tools.json");
    const validation = validateIntegrationManifest(manifest);

    expect(validation.ok).toBe(true);
    expect(validation.errors).toEqual([]);
    expect(manifest.tools).toEqual(
      expect.arrayContaining([
        expect.objectContaining({
          id: "pzprjs",
          tag: "v0.12.0",
          commit: "a104ecd6c0f2c982ffc3bbed16c66c24028dbbc5",
        }),
        expect.objectContaining({
          id: "noqx",
          tag: "v0.9.0",
          commit: "743a0a3e71702d1d66443b1b24153f7f201c1f57",
        }),
      ]),
    );
  });

  it("rejects tools without tag and commit pins", () => {
    const validation = validateIntegrationManifest({
      schemaVersion: 1,
      tools: [
        {
          id: "bad",
          kind: "solver-backend",
          repo: "https://example.com/bad.git",
          path: "integrations/bad",
          adapter: "src/pipeline/bad.ts",
          notes: "missing version pins",
        },
      ],
    });

    expect(validation.ok).toBe(false);
    expect(validation.errors).toContain("bad: tag is required");
    expect(validation.errors).toContain("bad: commit is required");
  });
});
