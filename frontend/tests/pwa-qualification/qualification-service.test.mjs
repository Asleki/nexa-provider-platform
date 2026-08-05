import test from "node:test";
import assert from "node:assert/strict";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { qualifyOfflinePwa } from "../../src/pwa/qualification/service.js";
import { formatQualificationReceipt } from "../../src/pwa/qualification/formatting.js";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("repository PWA produces a passing structured receipt", async () => {
  const receipt = await qualifyOfflinePwa({ frontendRoot: ROOT, qualificationId: "pwaqual:test", generatedAt: "2026-08-05T00:00:00Z", manualEvidence: { installationObserved: true, offlineReloadObserved: true, evidenceReference: "manual-mobile-session" } });
  assert.equal(receipt.status, "PASSED");
  assert.equal(receipt.milestoneId, "P003.5");
  assert.equal(receipt.databaseWritesPerformed, 0);
  assert.match(receipt.fingerprints.manifestSha256, /^[a-f0-9]{64}$/);
  assert.match(formatQualificationReceipt(receipt), /P003\.5 INSTALLATION AND OFFLINE QUALIFICATION/);
});
