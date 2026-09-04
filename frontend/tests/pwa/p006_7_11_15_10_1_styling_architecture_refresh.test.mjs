import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const swUrl = new URL("../../sw.js", import.meta.url);
const policyUrl = new URL("../../src/pwa/cache-policy.js", import.meta.url);

test(".15.10.1 preserves v17 while caching the shared governed snapshot loader", async () => {
  const [worker, policy] = await Promise.all([readFile(swUrl, "utf8"), readFile(policyUrl, "utf8")]);
  assert.match(worker, /CACHE_NAME = "nexilabs-shell-v17"/);
  assert.match(policy, /PWA_CACHE_VERSION = "nexilabs-shell-v17"/);
  assert.match(worker, /\.\/src\/map\/nngla\/governed-snapshot-loader\.js/);
  assert.match(policy, /\.\/src\/map\/nngla\/governed-snapshot-loader\.js/);
});

test(".15.10.1 has an explicit same-generation refresh marker and client navigation handoff", async () => {
  const worker = await readFile(swUrl, "utf8");
  assert.match(worker, /nexilabs-refresh-p006-7-11-15-10-1/);
  assert.match(worker, /STYLING_ARCHITECTURE_LOCK_SAME_GENERATION_REFRESH_MARKER/);
  assert.match(worker, /client\.navigate\(client\.url\)/);
});
