export type ParsedPzprUrl = {
  puzzleId: string;
  rows: number;
  cols: number;
  normalizedUrl: string;
  raw: unknown;
};

export type PzprAnswerCheck = {
  complete: boolean;
  message: string;
};

export type PzprAdapter = {
  parseUrl(url: string): Promise<ParsedPzprUrl>;
  normalizeUrl(url: string): Promise<string>;
  checkAnswer(url: string, answer: unknown): Promise<PzprAnswerCheck>;
};

export function createUnavailablePzprAdapter(): PzprAdapter {
  const fail = async (): Promise<never> => {
    throw new Error(
      "pzprjs adapter is not configured; install or vendor robx/pzprjs and provide a concrete adapter",
    );
  };

  return {
    parseUrl: fail,
    normalizeUrl: fail,
    checkAnswer: fail,
  };
}
