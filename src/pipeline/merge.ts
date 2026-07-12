import type {
  DatasetCaseRecord,
  DatasetFile,
  MergeReport,
  PipelineCaseResult,
} from "./types.js";

export function normalizeProblemKey(problem: string): string {
  const lines = problem.replace(/\r\n/g, "\n").replace(/\r/g, "\n").split("\n");
  return lines
    .map((line) => line.trim())
    .filter((line) => line !== "" || lines.length <= 1)
    .map((line) => line.split(/\s+/).filter(Boolean).join(" "))
    .join("\n")
    .trim();
}

function caseUrl(caseRecord: DatasetCaseRecord): string {
  return caseRecord.puzzlink_url?.trim() ?? "";
}

function cloneDataset(dataset: DatasetFile): DatasetFile {
  return {
    ...dataset,
    data: Object.fromEntries(
      Object.entries(dataset.data).map(([caseId, record]) => [
        caseId,
        { ...record },
      ]),
    ),
  };
}

function recount(dataset: DatasetFile): void {
  dataset.count = Object.keys(dataset.data).length;
  dataset.count_sol = Object.values(dataset.data).filter((record) =>
    record.solution.trim(),
  ).length;
}

export function mergePipelineResults(
  dataset: DatasetFile,
  results: PipelineCaseResult[],
): { dataset: DatasetFile; report: MergeReport } {
  const merged = cloneDataset(dataset);
  const existingUrls = new Set(
    Object.values(merged.data).map(caseUrl).filter((url) => url !== ""),
  );
  const existingProblems = new Set(
    Object.values(merged.data)
      .map((record) => normalizeProblemKey(record.problem))
      .filter((key) => key !== ""),
  );
  const usedIds = new Set(Object.keys(merged.data));

  const report: MergeReport = {
    added: 0,
    skippedUrlDup: 0,
    skippedProblemDup: 0,
    failed: 0,
    addedIds: [],
    failures: [],
  };

  for (const result of results) {
    if (result.status !== "solved") {
      report.failed += 1;
      if (report.failures.length < 50) {
        report.failures.push({
          caseId: result.caseId,
          reason: result.reason,
          sourceUrl: result.sourceUrl,
        });
      }
      continue;
    }

    const url = caseUrl(result.caseRecord);
    if (url !== "" && existingUrls.has(url)) {
      report.skippedUrlDup += 1;
      continue;
    }

    const problemKey = normalizeProblemKey(result.caseRecord.problem);
    if (problemKey !== "" && existingProblems.has(problemKey)) {
      report.skippedProblemDup += 1;
      continue;
    }

    let caseId = result.caseId;
    const baseId = caseId;
    for (let suffix = 1; usedIds.has(caseId); suffix += 1) {
      caseId = `${baseId}_${suffix}`;
    }

    merged.data[caseId] = { ...result.caseRecord };
    usedIds.add(caseId);
    if (url !== "") {
      existingUrls.add(url);
    }
    if (problemKey !== "") {
      existingProblems.add(problemKey);
    }
    report.added += 1;
    report.addedIds.push(caseId);
  }

  recount(merged);
  return { dataset: merged, report };
}
