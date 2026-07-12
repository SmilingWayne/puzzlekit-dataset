export type NoqxSolveRequestInput = {
  requestId: string;
  puzzleType: string;
  penpa: string;
  timeoutMs: number;
  maxSolutions: number;
};

export type NoqxSolveRequest = {
  requestId: string;
  puzzleType: string;
  penpa: string;
  options: {
    timeoutMs: number;
    maxSolutions: number;
  };
};

export type RawNoqxResponse = {
  url?: unknown;
  error?: unknown;
};

export type NormalizedNoqxResponse = {
  status: "solved" | "unsolved" | "multiple" | "failed";
  penpaSolutions: string[];
  reason?: string;
};

export function toNoqxSolveRequest(
  input: NoqxSolveRequestInput,
): NoqxSolveRequest {
  return {
    requestId: input.requestId,
    puzzleType: input.puzzleType,
    penpa: input.penpa,
    options: {
      timeoutMs: input.timeoutMs,
      maxSolutions: input.maxSolutions,
    },
  };
}

export function normalizeNoqxResponse(
  response: RawNoqxResponse,
): NormalizedNoqxResponse {
  if (typeof response.error === "string" && response.error.trim() !== "") {
    return {
      status: "failed",
      penpaSolutions: [],
      reason: response.error,
    };
  }

  const solutions = Array.isArray(response.url)
    ? response.url.filter((value): value is string => typeof value === "string")
    : [];

  if (solutions.length === 0) {
    return {
      status: "unsolved",
      penpaSolutions: [],
      reason: "no_solution",
    };
  }

  if (solutions.length > 1) {
    return {
      status: "multiple",
      penpaSolutions: solutions,
      reason: "multiple_solutions",
    };
  }

  return {
    status: "solved",
    penpaSolutions: solutions,
  };
}
