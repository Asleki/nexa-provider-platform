import test from "node:test";
import assert from "node:assert/strict";
import {
  BUNDLE_12F_BROWSER_CHECKS,
  BrowserQualificationStatus,
  createBrowserQualificationTemplate,
  evaluateBrowserQualificationEvidence,
} from "../../src/pwa/qualification/browser-ui-qualification.js";

test("P006.UI.18 exposes explicit manual browser checks instead of auto-claiming browser success", () => {
  const template = createBrowserQualificationTemplate();
  assert.equal(BUNDLE_12F_BROWSER_CHECKS.length, 8);
  assert.equal(Object.values(template).every((value) => value === null), true);
  assert.equal(evaluateBrowserQualificationEvidence(template).status, BrowserQualificationStatus.PENDING);
});

test("P006.UI.18 fails when any observed browser contract fails", () => {
  const evidence = Object.fromEntries(BUNDLE_12F_BROWSER_CHECKS.map(({ key }) => [key, true]));
  evidence.offlineReloadReady = false;
  const result = evaluateBrowserQualificationEvidence(evidence);
  assert.equal(result.status, BrowserQualificationStatus.FAILED);
  assert.equal(result.checks.find((check) => check.key === "offlineReloadReady").status, BrowserQualificationStatus.FAILED);
});

test("P006.UI.18 passes only when every required browser observation is explicitly true", () => {
  const evidence = Object.fromEntries(BUNDLE_12F_BROWSER_CHECKS.map(({ key }) => [key, true]));
  assert.equal(evaluateBrowserQualificationEvidence(evidence).status, BrowserQualificationStatus.PASSED);
});
