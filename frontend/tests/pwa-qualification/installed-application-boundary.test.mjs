import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import {
  inspectInstalledApplicationBoundary,
  resolveBootstrapDependencies,
  resolveInstalledApplicationBoundary,
} from "../../src/pwa/qualification/installed-application-boundary.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const manifest = JSON.parse(readFileSync(resolve(ROOT, "public/manifest.webmanifest"), "utf8"));
const manifestUrl = "http://127.0.0.1:8765/public/manifest.webmanifest";

test("P006.UI.16 resolves installed NexiLabs to the application root instead of /public/", () => {
  const result = inspectInstalledApplicationBoundary({ manifest, manifestUrl });
  assert.equal(result.expectedApplicationRoot, "http://127.0.0.1:8765/");
  assert.equal(result.idUrl, "http://127.0.0.1:8765/");
  assert.equal(result.startUrl, "http://127.0.0.1:8765/?source=pwa");
  assert.equal(result.scopeUrl, "http://127.0.0.1:8765/");
  assert.equal(result.escapedIntoPublicDirectory, false);
  assert.equal(result.passed, true);
});

test("P006.UI.16 would fail the exact historical ./ manifest defect", () => {
  const broken = { ...manifest, id: "./", start_url: "./?source=pwa", scope: "./" };
  const resolved = resolveInstalledApplicationBoundary({ manifest: broken, manifestUrl });
  assert.equal(resolved.startUrl, "http://127.0.0.1:8765/public/?source=pwa");
  const result = inspectInstalledApplicationBoundary({ manifest: broken, manifestUrl });
  assert.equal(result.escapedIntoPublicDirectory, true);
  assert.equal(result.passed, false);
});

test("P006.UI.16 root launch resolves the shell bootstrap dependency graph from frontend root", () => {
  const boundary = inspectInstalledApplicationBoundary({ manifest, manifestUrl });
  const dependencies = resolveBootstrapDependencies({ launchUrl: boundary.startUrl });
  assert.deepEqual(dependencies, {
    stylesheet: "http://127.0.0.1:8765/styles/app.css",
    mainModule: "http://127.0.0.1:8765/src/main.js",
    manifest: "http://127.0.0.1:8765/public/manifest.webmanifest",
    serviceWorker: "http://127.0.0.1:8765/sw.js",
  });
});

test("P006.UI.16 remains deployment-path relative rather than localhost-specific", () => {
  const result = inspectInstalledApplicationBoundary({
    manifest,
    manifestUrl: "https://example.test/nexilabs/public/manifest.webmanifest",
  });
  assert.equal(result.startUrl, "https://example.test/nexilabs/?source=pwa");
  assert.equal(result.scopeUrl, "https://example.test/nexilabs/");
  assert.equal(result.passed, true);
});
