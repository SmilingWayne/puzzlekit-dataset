import { readFileSync } from "node:fs";

export function loadIntegrationManifest(path) {
  return JSON.parse(readFileSync(path, "utf8"));
}

export function validateIntegrationManifest(manifest) {
  const errors = [];
  const ids = new Set();

  for (const tool of manifest.tools) {
    if (ids.has(tool.id)) {
      errors.push(`${tool.id}: duplicate id`);
    }
    ids.add(tool.id);

    for (const field of ["kind", "repo", "path", "adapter", "notes"]) {
      if (!tool[field]?.trim()) {
        errors.push(`${tool.id}: ${field} is required`);
      }
    }
    if (!tool.tag?.trim()) {
      errors.push(`${tool.id}: tag is required`);
    }
    if (!tool.commit?.trim()) {
      errors.push(`${tool.id}: commit is required`);
    }
    if (tool.commit && !/^[0-9a-f]{40}$/i.test(tool.commit)) {
      errors.push(`${tool.id}: commit must be a 40 character SHA`);
    }
  }

  return {
    ok: errors.length === 0,
    errors,
  };
}
