import type {
  NormalizedNoqxResponse,
  NoqxSolveRequest,
} from "./noqx.js";

export type SolverBackend = {
  id: string;
  solve(request: NoqxSolveRequest): Promise<NormalizedNoqxResponse>;
};

export type SolverBackendRegistry = {
  get(id: string): SolverBackend;
  defaultBackend(): SolverBackend;
};

export function createSolverBackendRegistry(input: {
  defaultBackendId: string;
  backends: SolverBackend[];
}): SolverBackendRegistry {
  const backends = new Map(input.backends.map((backend) => [backend.id, backend]));

  return {
    get(id) {
      const backend = backends.get(id);
      if (!backend) {
        throw new Error(`Solver backend '${id}' is not registered`);
      }
      return backend;
    },
    defaultBackend() {
      return this.get(input.defaultBackendId);
    },
  };
}
