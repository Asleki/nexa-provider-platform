/** P003.5 — Application-shell and install metadata qualification rules. */
import { existsSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { createFinding } from "./contracts.js";
import { resolveLocalAsset } from "./source-inspector.js";
import { inspectInstalledApplicationBoundary, resolveBootstrapDependencies } from "./installed-application-boundary.js";

const unique = (values) => [...new Set(values)];

export function qualifyManifest(manifest, frontendRoot, { manifestUrl = "https://nexilabs.invalid/public/manifest.webmanifest" } = {}) {
  const findings = [];
  const required = ["id", "name", "short_name", "start_url", "scope", "display", "icons"];
  findings.push(createFinding({ code: "MANIFEST_REQUIRED_FIELDS", passed: required.every((key) => key in manifest), message: "Manifest contains all governed install fields." }));

  let boundary = null;
  try { boundary = inspectInstalledApplicationBoundary({ manifest, manifestUrl }); } catch {}
  findings.push(createFinding({
    code: "MANIFEST_APPLICATION_ROOT",
    passed: Boolean(boundary?.passed),
    message: "Manifest id, start URL and scope resolve to the NexiLabs application root rather than the public asset directory.",
    details: boundary ?? { manifestUrl }
  }));

  let bootstrap = null;
  if (boundary?.passed) bootstrap = resolveBootstrapDependencies({ launchUrl: boundary.startUrl });
  const expectedRoot = boundary ? new URL(boundary.expectedApplicationRoot) : null;
  const bootstrapInsideRoot = bootstrap && expectedRoot
    ? Object.values(bootstrap).every((value) => { const url = new URL(value); return url.origin === expectedRoot.origin && url.pathname.startsWith(expectedRoot.pathname); })
    : false;
  findings.push(createFinding({
    code: "INSTALLED_BOOTSTRAP_ROOT",
    passed: Boolean(bootstrapInsideRoot),
    message: "Installed launch resolves the stylesheet, main module, manifest and service worker from the application root.",
    details: bootstrap ?? {}
  }));

  findings.push(createFinding({ code: "MANIFEST_STANDALONE_DISPLAY", passed: manifest.display === "standalone", message: "Manifest requests standalone display mode." }));
  const icons = Array.isArray(manifest.icons) ? manifest.icons : [];
  const purposes = new Set(icons.map((icon) => icon.purpose));
  findings.push(createFinding({ code: "MANIFEST_ICON_PURPOSES", passed: purposes.has("any") && purposes.has("maskable"), message: "Manifest declares ordinary and maskable icons." }));
  const manifestRoot = resolve(frontendRoot, "public");
  const missing = icons.filter((icon) => !existsSync(resolve(manifestRoot, icon.src.replace(/^\.\//, "")))).map((icon) => icon.src);
  findings.push(createFinding({ code: "MANIFEST_ICONS_EXIST", passed: missing.length === 0, message: "Every declared manifest icon exists.", details: { missing } }));
  return findings;
}

export function qualifyShellInventory({ workerAssets, policyAssets, workerCacheVersion, policyCacheVersion, workerOfflineDocument, policyOfflineDocument, registrationUsesPolicyGeneration }, frontendRoot) {
  const findings = [];
  const workerUnique = unique(workerAssets);
  const policyUnique = unique(policyAssets);
  findings.push(createFinding({ code: "CACHE_VERSION_PARITY", passed: workerCacheVersion === policyCacheVersion, message: "Worker and cache policy use the same cache version.", details: { workerCacheVersion, policyCacheVersion } }));
  findings.push(createFinding({ code: "SHELL_GENERATION_SINGLE_SOURCE", passed: registrationUsesPolicyGeneration === true, message: "Browser registration derives its announced shell generation from the cache policy instead of duplicating a stale version literal." }));
  findings.push(createFinding({ code: "OFFLINE_DOCUMENT_PARITY", passed: workerOfflineDocument === policyOfflineDocument, message: "Worker and cache policy use the same offline document." }));
  findings.push(createFinding({ code: "SHELL_INVENTORY_PARITY", passed: JSON.stringify(workerAssets) === JSON.stringify(policyAssets), message: "Worker and policy shell inventories match exactly." }));
  findings.push(createFinding({ code: "SHELL_INVENTORY_UNIQUE", passed: workerUnique.length === workerAssets.length && policyUnique.length === policyAssets.length, message: "Shell inventories contain no duplicate paths." }));
  const unsafe = workerAssets.filter((asset) => !asset.startsWith("./") || asset.includes("..") || /^https?:/i.test(asset));
  findings.push(createFinding({ code: "SHELL_PATHS_LOCAL", passed: unsafe.length === 0, message: "Shell inventory contains only safe local paths.", details: { unsafe } }));
  const missing = [];
  for (const asset of workerUnique) {
    if (!asset.startsWith("./") || asset.includes("..") || /^https?:/i.test(asset)) { missing.push(asset); continue; }
    const path = resolveLocalAsset(frontendRoot, asset);
    if (!existsSync(path) || !statSync(path).isFile()) missing.push(asset);
  }
  findings.push(createFinding({ code: "SHELL_ASSETS_EXIST", passed: missing.length === 0, message: "Every pre-cached application-shell asset exists.", details: { missing } }));
  const forbidden = workerAssets.filter((asset) => /roadmap|postgres|database|nexapos/i.test(asset));
  findings.push(createFinding({ code: "SHELL_BOUNDARY_ISOLATED", passed: forbidden.length === 0, message: "Shell cache excludes roadmap, database and NexaPOS resources.", details: { forbidden } }));
  return findings;
}
