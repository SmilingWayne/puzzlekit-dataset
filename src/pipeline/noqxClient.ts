import {
  type NormalizedNoqxResponse,
  type NoqxSolveRequest,
  normalizeNoqxResponse,
} from "./noqx.js";
import type { SolverBackend } from "./solverBackend.js";

type FetchLike = (
  url: string,
  init: {
    method: "POST";
    headers: Record<string, string>;
    body: string;
  },
) => Promise<Response>;

export type NoqxHttpClientOptions = {
  baseUrl: string;
  fetch?: FetchLike;
};

export type NoqxHttpClient = SolverBackend;

function solveUrl(baseUrl: string): string {
  return `${baseUrl.replace(/\/+$/, "")}/solve`;
}

export function createNoqxHttpClient(
  options: NoqxHttpClientOptions,
): NoqxHttpClient {
  const fetchImpl = options.fetch ?? fetch;

  return {
    id: "noqx-http",
    async solve(request) {
      const response = await fetchImpl(solveUrl(options.baseUrl), {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const text = await response.text();
        return {
          status: "failed",
          penpaSolutions: [],
          reason: `sidecar_http_${response.status}:${text}`,
        };
      }

      const body = (await response.json()) as unknown;
      return normalizeNoqxResponse(
        typeof body === "object" && body !== null ? body : {},
      );
    },
  };
}
