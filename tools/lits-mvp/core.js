import { readFileSync, writeFileSync } from "node:fs";
import { spawnSync } from "node:child_process";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

export function parseLitsProblemFromPzprFileData(fileData) {
  const lines = fileData
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line !== "");

  if (lines[0] !== "pzprv3" || lines[1] !== "lits") {
    throw new Error("Expected pzprv3 LITS file data");
  }

  const rows = Number.parseInt(lines[2], 10);
  const cols = Number.parseInt(lines[3], 10);
  if (!Number.isInteger(rows) || !Number.isInteger(cols)) {
    throw new Error("Invalid LITS row/col header in pzpr file data");
  }

  const regionRows = lines.slice(5, 5 + rows).map((line) =>
    line
      .split(/\s+/)
      .filter(Boolean)
      .join(" "),
  );
  if (regionRows.length !== rows) {
    throw new Error(`Expected ${rows} LITS region rows, got ${regionRows.length}`);
  }

  for (const row of regionRows) {
    const width = row.split(/\s+/).filter(Boolean).length;
    if (width !== cols) {
      throw new Error(`Expected ${cols} columns in LITS region row, got ${width}`);
    }
  }

  return [`${rows} ${cols}`, ...regionRows].join("\n");
}

export function buildCaseRecord({ problem, solution, puzzlinkUrl }) {
  return {
    problem,
    solution,
    source: "",
    info: "",
    puzzlink_url: puzzlinkUrl,
  };
}

export function appendCases(dataset, cases) {
  const next = {
    ...dataset,
    data: Object.fromEntries(
      Object.entries(dataset.data ?? {}).map(([caseId, record]) => [
        caseId,
        { ...record },
      ]),
    ),
  };

  const usedIds = new Set(Object.keys(next.data));
  for (const item of cases) {
    let caseId = item.caseId;
    const baseId = caseId;
    for (let suffix = 1; usedIds.has(caseId); suffix += 1) {
      caseId = `${baseId}_${suffix}`;
    }
    next.data[caseId] = { ...item.record };
    usedIds.add(caseId);
  }

  next.count = Object.keys(next.data).length;
  next.count_sol = Object.values(next.data).filter((record) =>
    String(record.solution ?? "").trim(),
  ).length;
  return next;
}

export function loadLitsEntriesFromCsv(csvPath, limit) {
  const [headerLine, ...rows] = readFileSync(csvPath, "utf8")
    .split(/\r?\n/)
    .filter((line) => line.trim() !== "");
  const headers = headerLine.split(",");
  const entries = [];

  for (const line of rows) {
    const values = line.split(",");
    const row = Object.fromEntries(headers.map((header, index) => [header, values[index] ?? ""]));
    if (row.puzzle_type !== "lits") {
      continue;
    }
    entries.push({
      name: row.name,
      puzzlinkUrl: row.puzz_link_url,
    });
    if (limit > 0 && entries.length >= limit) {
      break;
    }
  }

  return entries;
}

export function createPzprLitsDecoder(pzprPath = "../../integrations/pzprjs") {
  const pzpr = require(pzprPath);
  return {
    decodeProblem(url) {
      const puzzle = new pzpr.Puzzle({ type: "player" }).open(url);
      if (puzzle.pid !== "lits") {
        throw new Error(`Expected LITS puzzle, got '${puzzle.pid}'`);
      }
      return parseLitsProblemFromPzprFileData(puzzle.getFileData());
    },
  };
}

export function solveLitsWithPython({ pythonPath, bridgePath, problem, timeLimitSec }) {
  const result = spawnSync(
    pythonPath,
    [bridgePath],
    {
      input: JSON.stringify({ problem, timeLimitSec }),
      encoding: "utf8",
      env: {
        ...process.env,
        MPLCONFIGDIR: ".cache/matplotlib",
      },
    },
  );

  if (result.status !== 0) {
    throw new Error(result.stderr.trim() || `Python solver exited with ${result.status}`);
  }

  const payload = JSON.parse(result.stdout);
  if (!payload.ok) {
    throw new Error(payload.error || "LITS solver failed");
  }
  return payload.solution;
}

export function readDataset(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function writeDataset(path, dataset) {
  writeFileSync(path, `${JSON.stringify(dataset, null, 2)}\n`, "utf8");
}
