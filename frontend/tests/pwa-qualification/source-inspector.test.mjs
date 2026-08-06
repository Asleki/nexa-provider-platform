import test from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { inspectDeclaredPwaSources } from "../../src/pwa/qualification/source-inspector.js";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("worker and policy declarations are extracted deterministically", () => {
  const result = inspectDeclaredPwaSources(ROOT);
  assert.equal(result.workerCacheVersion, "novegeo-shell-v2");
  assert.equal(result.policyCacheVersion, "novegeo-shell-v2");
  assert.deepEqual(result.workerAssets, result.policyAssets);
  assert.equal(result.workerOfflineDocument, "./index.html");
});
