import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");
const policy = readFileSync(resolve(ROOT, "src/pwa/cache-policy.js"), "utf8");

const liveModules = [
  "./src/app/features/novegeo-live-authority-runtime.js",
  "./src/config/live-api-endpoint.js",
  "./src/map/geography/live-boundary-client.js",
  "./src/map/nngla/live-contracts.js",
  "./src/map/nngla/live-read-client.js",
  "./src/map/nngla/live-publication-status.js",
];

test("Bundle 18 adds the live-authority module graph to the existing v17 shell cache", () => {
  for (const marker of liveModules) {
    assert.ok(worker.includes(marker), marker);
    assert.ok(policy.includes(marker), marker);
  }
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
});

test("Bundle 18 shell caching contains no database credentials or PostgreSQL connection string", () => {
  assert.doesNotMatch(worker, /PGPASSWORD|PGHOST|postgresql:\/\//i);
  assert.doesNotMatch(policy, /PGPASSWORD|PGHOST|postgresql:\/\//i);
});
