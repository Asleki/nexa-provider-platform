import test from "node:test";
import assert from "node:assert/strict";
import { createFinding, createQualificationReceipt } from "../../src/pwa/qualification/contracts.js";

test("qualification receipt fails when any finding fails", () => {
  const receipt = createQualificationReceipt({
    qualificationId: "pwaqual:test", generatedAt: "2026-08-05T00:00:00Z",
    applicationVersion: "0.1.0", cacheVersion: "novegeo-shell-v1",
    fingerprints: {}, findings: [createFinding({ code: "ONE", passed: true, message: "ok" }), createFinding({ code: "TWO", passed: false, message: "bad" })],
    manualEvidence: {}
  });
  assert.equal(receipt.status, "FAILED");
  assert.equal(receipt.databaseWritesPerformed, 0);
});
