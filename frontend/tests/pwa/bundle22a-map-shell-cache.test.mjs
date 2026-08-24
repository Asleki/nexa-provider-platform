import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");
const policy = readFileSync(resolve(ROOT, "src/pwa/cache-policy.js"), "utf8");
const bundle22aAssets = [
  "./styles/novegeo-map-shell-v1.css",
  "./src/app/features/novegeo-map-shell-hardening-runtime.js",
  "./src/map/controls/novegeo-map-shell.js",
  "./src/map/controls/national-layer-status.js",
  "./src/map/validation/map-shell-safe-area.js",
];

test("Bundle 22A appends its additive map-shell graph to worker-policy cache parity", () => {
  for (const marker of bundle22aAssets) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
});

test("Bundle 22A cache additions contain no PostgreSQL credentials or database connection strings", () => {
  assert.doesNotMatch(worker, /PGPASSWORD|PGHOST|postgresql:\/\//i);
  assert.doesNotMatch(policy, /PGPASSWORD|PGHOST|postgresql:\/\//i);
});
