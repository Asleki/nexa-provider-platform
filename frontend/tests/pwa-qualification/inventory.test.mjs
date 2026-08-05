import test from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { readJson, inspectDeclaredPwaSources } from "../../src/pwa/qualification/source-inspector.js";
import { qualifyManifest, qualifyShellInventory } from "../../src/pwa/qualification/inventory.js";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("current install manifest and shell inventory qualify cleanly", () => {
  const manifest = readJson(resolve(ROOT, "public/manifest.webmanifest"));
  const findings = [...qualifyManifest(manifest, ROOT), ...qualifyShellInventory(inspectDeclaredPwaSources(ROOT), ROOT)];
  assert.ok(findings.length >= 10);
  assert.ok(findings.every((finding) => finding.passed), findings.filter((finding) => !finding.passed));
});

test("unsafe remote shell path is rejected", () => {
  const findings = qualifyShellInventory({
    workerAssets: ["https://example.test/app.js"], policyAssets: ["https://example.test/app.js"],
    workerCacheVersion: "v1", policyCacheVersion: "v1", workerOfflineDocument: "./index.html", policyOfflineDocument: "./index.html"
  }, ROOT);
  assert.equal(findings.find((f) => f.code === "SHELL_PATHS_LOCAL").passed, false);
});
