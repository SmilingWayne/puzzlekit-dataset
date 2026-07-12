#!/usr/bin/env node
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";

import { loadIntegrationManifest } from "./manifest.js";

const manifest = loadIntegrationManifest("integrations/tools.json");

for (const tool of manifest.tools) {
  if (!existsSync(tool.path)) {
    console.log(`${tool.id}: missing (${tool.path}) target=${tool.tag}`);
    continue;
  }

  const result = spawnSync(
    "git",
    ["-C", tool.path, "rev-parse", "--short", "HEAD"],
    {
      encoding: "utf8",
    },
  );
  const head = result.status === 0 ? result.stdout.trim() : "unknown";
  console.log(`${tool.id}: ${tool.path} head=${head} target=${tool.tag}`);
}
