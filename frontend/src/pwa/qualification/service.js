/** P003.5 — Read-only installation and offline qualification service. */
import { createHash, randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";
import { createFinding, createQualificationReceipt } from "./contracts.js";
import { inspectDeclaredPwaSources, readJson } from "./source-inspector.js";
import { qualifyManifest, qualifyShellInventory } from "./inventory.js";
import { MemoryCacheStorage, simulateActivationCleanup, simulateOfflineQualification } from "./offline-simulator.js";

const sha256 = (value) => createHash("sha256").update(value).digest("hex");

export async function qualifyOfflinePwa({ frontendRoot, qualificationId = `pwaqual:${randomUUID()}`, generatedAt = new Date().toISOString(), manualEvidence = {} }) {
  const manifestPath = resolve(frontendRoot, "public/manifest.webmanifest");
  const manifestText = readFileSync(manifestPath, "utf8");
  const manifest = readJson(manifestPath);
  const sources = inspectDeclaredPwaSources(frontendRoot);
  const findings = [
    ...qualifyManifest(manifest, frontendRoot),
    ...qualifyShellInventory(sources, frontendRoot)
  ];
  const storage = new MemoryCacheStorage({ "novegeo-shell-old": { "./index.html": "old" } });
  const offline = await simulateOfflineQualification({ cacheStorage: storage, cacheName: sources.workerCacheVersion, shellAssets: sources.workerAssets, offlineDocument: sources.workerOfflineDocument });
  findings.push(createFinding({ code: "OFFLINE_NAVIGATION_AVAILABLE", passed: offline.passed, message: "The approved offline document is available after shell pre-cache.", details: offline }));
  const cleanup = await simulateActivationCleanup(storage, sources.workerCacheVersion);
  findings.push(createFinding({ code: "STALE_CACHE_CLEANUP", passed: cleanup.passed, message: "Activation cleanup retains only the current NoveGeo shell cache.", details: cleanup }));
  const html = readFileSync(resolve(frontendRoot, "index.html"), "utf8");
  findings.push(createFinding({ code: "OFFLINE_SHELL_IDENTITY", passed: html.includes("NexiLabs NoveGeo PWA") && html.includes('id="nexilabs-app"'), message: "Offline fallback contains stable NoveGeo shell identity markers." }));
  findings.push(createFinding({ code: "MANUAL_INSTALL_EVIDENCE_BOUNDARY", passed: manualEvidence.installationObserved !== false, message: "Manual browser installation evidence is recorded separately from repository qualification.", details: manualEvidence }));
  return createQualificationReceipt({
    qualificationId,
    generatedAt,
    applicationVersion: manifest.version || "0.1.0",
    cacheVersion: sources.workerCacheVersion,
    fingerprints: {
      manifestSha256: sha256(manifestText),
      serviceWorkerSha256: sha256(sources.workerSource),
      cachePolicySha256: sha256(sources.policySource),
      shellInventorySha256: sha256(JSON.stringify(sources.workerAssets))
    },
    findings,
    manualEvidence: { installationObserved: manualEvidence.installationObserved ?? null, offlineReloadObserved: manualEvidence.offlineReloadObserved ?? null, evidenceReference: manualEvidence.evidenceReference ?? null }
  });
}
