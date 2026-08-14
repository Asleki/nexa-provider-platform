import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const runtime = readFileSync(resolve(ROOT, "src/app/features/novegeo-feature-runtime.js"), "utf8");
const status = readFileSync(resolve(ROOT, "src/map/nngla/publication-status.js"), "utf8");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");

test("P006.7.9 integrates NNGLA as an additive read-only status adapter without a second map engine", () => {
  assert.match(runtime, /mountNnglaPublicationStatus/);
  assert.match(status, /Governed CSV sources are distinct from PostgreSQL canonical/i);
  assert.match(status, /offline base map remains available/i);
  assert.doesNotMatch(status, /\b(?:POST|PUT|PATCH|DELETE)\b|postgres(?:ql)?:\/\/|password=/i);
});

test("Bundle 15.0D advances the installed shell generation and pre-caches the NNGLA module graph", () => {
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  for (const asset of ["contracts.js", "read-client.js", "render-plan.js", "publication-status.js"]) assert.match(worker, new RegExp(`src/map/nngla/${asset.replace(/[.]/g, "\\.")}`));
  assert.match(worker, /previousShellKeys/);
  assert.match(worker, /client\.navigate\(client\.url\)/);
});
