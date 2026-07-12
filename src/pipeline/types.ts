export type DatasetCaseRecord = {
  problem: string;
  solution: string;
  source?: string;
  info?: string;
  puzzlink_url?: string;
};

export type DatasetFile = {
  name: string;
  count: number;
  count_sol: number;
  data: Record<string, DatasetCaseRecord>;
};

export type PipelineCaseResult =
  | {
      status: "solved";
      caseId: string;
      caseRecord: DatasetCaseRecord;
    }
  | {
      status: "failed" | "skipped";
      caseId?: string;
      reason: string;
      sourceUrl?: string;
    };

export type MergeReport = {
  added: number;
  skippedUrlDup: number;
  skippedProblemDup: number;
  failed: number;
  addedIds: string[];
  failures: Array<{
    caseId?: string;
    reason: string;
    sourceUrl?: string;
  }>;
};
