/** P003.5 — Application-shell and install metadata qualification rules. */
import { existsSync, statSync } from "node:fs";
import { resolve } from "node:path";
import { createFinding } from "./contracts.js";
import { resolveLocalAsset } from "./source-inspector.js";

const unique = (values) => [...new Set(values)];

export function qualifyManifest(manifest, frontendRoot) {
  const findings = [];
  const required = ["name", "short_name", "start_url", "scope", "display", "icons"];
  findings.push(createFinding({ code: "MANIFEST_REQUIRED_FIELDS", passed: required.every((key) => key in manifest), message: "Manifest contains all governed install fields." }));
  findings.push(createFinding({ code: "MANIFEST_LOCAL_SCOPE", passed: manifest.start_url?.startsWith("./") && manifest.scope === "./", message: "Manifest start URL and scope remain local to the NoveGeo PWA." }));
  findings.push(createFinding({ code: "MANIFEST_STANDALONE_DISPLAY", passed: manifest.display === "standalone", message: "Manifest requests standalone display mode." }));
  const icons = Array.isArray(manifest.icons) ? manifest.icons : [];
  const purposes = new Set(icons.map((icon) => icon.purpose));
  findings.push(createFinding({ code: "MANIFEST_ICON_PURPOSES", passed: purposes.has("any") && purposes.has("maskable"), message: "Manifest declares ordinary and maskable icons." }));
  const manifestRoot = resolve(frontendRoot, "public");
  const missing = icons.filter((icon) => !existsSync(resolve(manifestRoot, icon.src.replace(/^\.\//, "")))).map((icon) => icon.src);
  findings.push(createFinding({ code: "MANIFEST_ICONS_EXIST", passed: missing.length === 0, message: "Every declared manifest icon exists.", details: { missing } }));
  return findings;
}

export function qualifyShellInventory({ workerAssets, policyAssets, workerCacheVersion, policyCacheVersion, workerOfflineDocument, policyOfflineDocument }, frontendRoot) {
  const findings = [];
  const workerUnique = unique(workerAssets);
  const policyUnique = unique(policyAssets);
  findings.push(createFinding({ code: "CACHE_VERSION_PARITY", passed: workerCacheVersion === policyCacheVersion, message: "Worker and cache policy use the same cache version.", details: { workerCacheVersion, policyCacheVersion } }));
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
