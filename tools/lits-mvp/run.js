#!/usr/bin/env node
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

import {
  appendCases,
  buildCaseRecord,
  createPzprLitsDecoder,
  loadLitsEntriesFromCsv,
  readDataset,
  solveLitsWithPython,
  writeDataset,
} from "./core.js";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

function parseArgs(argv) {
  const args = {
    limit: 1,
    write: false,
    timeLimitSec: 20,
    csv: resolve(root, "puzzlink_crawlers/logs/merged_puzzles.csv"),
    dataset: resolve(root, "assets/data/LITS/LITS_dataset.json"),
    python: resolve(root, ".venv/bin/python"),
    bridge: resolve(root, "tools/lits-mvp/solve_lits.py"),
  };

  for (let index = 0; index < argv.length; index += 1) {
    const arg = argv[index];
    if (arg === "--write") {
      args.write = true;
    } else if (arg === "--limit") {
      args.limit = Number.parseInt(argv[++index], 10);
    } else if (arg === "--time-limit") {
      args.timeLimitSec = Number.parseFloat(argv[++index]);
    } else if (arg === "--csv") {
      args.csv = resolve(argv[++index]);
    } else if (arg === "--dataset") {
      args.dataset = resolve(argv[++index]);
    } else if (arg === "--python") {
      args.python = resolve(argv[++index]);
    }
  }

  return args;
}

function main() {
  const args = parseArgs(process.argv.slice(2));
  const entries = loadLitsEntriesFromCsv(args.csv, args.limit);
  const decoder = createPzprLitsDecoder(resolve(root, "integrations/pzprjs"));

  const cases = [];
  const failures = [];
  for (const entry of entries) {
    try {
      const problem = decoder.decodeProblem(entry.puzzlinkUrl);
      const solution = solveLitsWithPython({
        pythonPath: args.python,
        bridgePath: args.bridge,
        problem,
        timeLimitSec: args.timeLimitSec,
      });
      cases.push({
        caseId: entry.name,
        record: buildCaseRecord({
          problem,
          solution,
          puzzlinkUrl: entry.puzzlinkUrl,
        }),
      });
    } catch (error) {
      failures.push({
        caseId: entry.name,
        url: entry.puzzlinkUrl,
        error: error instanceof Error ? error.message : String(error),
      });
    }
  }

  const dataset = readDataset(args.dataset);
  const next = appendCases(dataset, cases);
  if (args.write) {
    writeDataset(args.dataset, next);
  }

  const report = {
    puzzle: "lits",
    csv: args.csv,
    dataset: args.dataset,
    write: args.write,
    requested: entries.length,
    solved: cases.length,
    failed: failures.length,
    addedIds: cases.map((item) => item.caseId),
    failures,
    countBefore: dataset.count,
    countAfter: next.count,
    countSolBefore: dataset.count_sol,
    countSolAfter: next.count_sol,
  };

  console.log(JSON.stringify(report, null, 2));
  return failures.length === 0 ? 0 : 1;
}

process.exitCode = main();
