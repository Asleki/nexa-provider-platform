import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");
const policy = readFileSync(resolve(ROOT, "src/pwa/cache-policy.js"), "utf8");

test("service worker implements install, activate, message and fetch lifecycles", () => {
  for (const event of ["install", "activate", "message", "fetch"]) {
    assert.ok(worker.includes(`addEventListener("${event}"`), event);
  }
  assert.match(worker, /cache\.addAll\(APP_SHELL\)/);
  assert.match(worker, /self\.clients\.claim\(\)/);
  assert.match(worker, /self\.skipWaiting\(\)/);
});

test("offline navigation fallback and same-origin GET boundary are explicit", () => {
  assert.match(worker, /request\.method !== "GET"/);
  assert.match(worker, /url\.origin !== self\.location\.origin/);
  assert.match(worker, /request\.mode === "navigate"/);
  assert.match(worker, /caches\.match\(OFFLINE_URL\)/);
});

test("cache version and shell inventory are versioned", () => {
  assert.match(policy, /PWA_CACHE_VERSION = "novegeo-shell-v8"/);
  assert.match(policy, /APPLICATION_SHELL_ASSETS/);
  assert.match(worker, /CACHE_NAME = "novegeo-shell-v8"/);
  assert.match(worker, /keys\.filter\(\(key\) => key !== CACHE_NAME\)/);
});
