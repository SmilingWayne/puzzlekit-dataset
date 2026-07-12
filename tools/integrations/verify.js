#!/usr/bin/env node
import { existsSync } from "node:fs";
import { spawnSync } from "node:child_process";

import {
  loadIntegrationManifest,
  validateIntegrationManifest,
} from "./manifest.js";

const manifest = loadIntegrationManifest("integrations/tools.json");
const validation = validateIntegrationManifest(manifest);

if (!validation.ok) {
  for (const error of validation.errors) {
    console.error(error);
  }
  process.exit(1);
}

let ok = true;
for (const tool of manifest.tools) {
  if (!existsSync(tool.path)) {
    console.warn(`${tool.id}: ${tool.path} is not checked out yet`);
    continue;
  }

  const result = spawnSync("git", ["-C", tool.path, "rev-parse", "HEAD"], {
    encoding: "utf8",
  });
  if (result.status !== 0) {
    ok = false;
    console.error(`${tool.id}: unable to read git HEAD at ${tool.path}`);
    continue;
  }

  const actual = result.stdout.trim();
  if (actual !== tool.commit) {
    ok = false;
    console.error(
      `${tool.id}: expected ${tool.commit} (${tool.tag}), found ${actual}`,
    );
  } else {
    console.log(`${tool.id}: ${tool.tag} ${tool.commit}`);
  }
}

if (!ok) {
  process.exit(1);
}
