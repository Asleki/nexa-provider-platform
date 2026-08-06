import test from "node:test";
import assert from "node:assert/strict";
import { createValidationFinding, QualificationStatus } from "../../../src/map/validation/contracts.js";

test("validation findings are immutable and classify failures", () => {
  const finding = createValidationFinding({ code: "TEST", passed: false, message: "failed", details: { reason: "x" } });
  assert.equal(finding.severity, "ERROR");
  assert.equal(QualificationStatus.PASSED, "PASSED");
  assert.ok(Object.isFrozen(finding));
});
