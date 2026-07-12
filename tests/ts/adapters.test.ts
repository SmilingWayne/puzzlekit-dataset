import { describe, expect, it } from "vitest";

import { createNoqxHttpClient } from "../../src/pipeline/noqxClient.js";
import { createUnavailablePzprAdapter } from "../../src/pipeline/pzprAdapter.js";

describe("pzpr adapter boundary", () => {
  it("fails with an actionable message before pzprjs is wired", async () => {
    const adapter = createUnavailablePzprAdapter();

    await expect(
      adapter.parseUrl("https://puzz.link/p?masyu/2/2/a"),
    ).rejects.toThrow("pzprjs adapter is not configured");
  });
});

describe("noqx HTTP sidecar client", () => {
  it("posts solve requests and normalizes noqx responses", async () => {
    const requests: unknown[] = [];
    const client = createNoqxHttpClient({
      baseUrl: "http://127.0.0.1:8765",
      fetch: async (url, init) => {
        requests.push({ url, init });
        return new Response(JSON.stringify({ url: ["penpa-solution"] }), {
          status: 200,
          headers: { "content-type": "application/json" },
        });
      },
    });

    expect(client.id).toBe("noqx-http");

    const response = await client.solve({
      requestId: "case-1",
      puzzleType: "masyu",
      penpa: "m=edit&p=abc",
      options: {
        timeoutMs: 30_000,
        maxSolutions: 2,
      },
    });

    expect(response).toEqual({
      status: "solved",
      penpaSolutions: ["penpa-solution"],
    });
    expect(requests).toHaveLength(1);
    expect(requests[0]).toMatchObject({
      url: "http://127.0.0.1:8765/solve",
      init: {
        method: "POST",
        headers: { "content-type": "application/json" },
      },
    });
  });

  it("turns non-2xx sidecar responses into failed solution statuses", async () => {
    const client = createNoqxHttpClient({
      baseUrl: "http://127.0.0.1:8765/",
      fetch: async () =>
        new Response("boom", {
          status: 500,
        }),
    });

    await expect(
      client.solve({
        requestId: "case-1",
        puzzleType: "masyu",
        penpa: "m=edit&p=abc",
        options: {
          timeoutMs: 30_000,
          maxSolutions: 2,
        },
      }),
    ).resolves.toEqual({
      status: "failed",
      penpaSolutions: [],
      reason: "sidecar_http_500:boom",
    });
  });
});
