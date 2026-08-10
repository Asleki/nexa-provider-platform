/** P006.UI.18 — Manual browser evidence contract kept separate from repository-only qualification. */
export const BrowserQualificationStatus = Object.freeze({
  PENDING: "PENDING",
  PASSED: "PASSED",
  FAILED: "FAILED",
});

export const BUNDLE_12F_BROWSER_CHECKS = Object.freeze([
  Object.freeze({ key: "freshInstallLaunchesApplicationRoot", label: "Fresh installed PWA launches the NexiLabs application root" }),
  Object.freeze({ key: "styledShellReady", label: "Installed PWA reaches the fully styled NexiLabs READY shell" }),
  Object.freeze({ key: "standaloneReloadReady", label: "Standalone PWA reload returns to a usable shell" }),
  Object.freeze({ key: "offlineReloadReady", label: "Offline standalone reload returns the cached application shell" }),
  Object.freeze({ key: "simulationBoundaryPreserved", label: "Simulation routes remain Simulation after install/reload" }),
  Object.freeze({ key: "productionAuthorizationPreserved", label: "Production routes retain authentication and authorization guards" }),
  Object.freeze({ key: "noveGeoControlsReady", label: "NoveGeo pan, zoom, reset, layers and search remain usable" }),
  Object.freeze({ key: "resizeOrientationReady", label: "NoveGeo remains geometrically coherent after resize/orientation change" }),
]);

export function createBrowserQualificationTemplate() {
  return Object.freeze(Object.fromEntries(BUNDLE_12F_BROWSER_CHECKS.map(({ key }) => [key, null])));
}

export function evaluateBrowserQualificationEvidence(evidence = {}) {
  const checks = BUNDLE_12F_BROWSER_CHECKS.map(({ key, label }) => {
    const value = evidence[key];
    const status = value === true ? BrowserQualificationStatus.PASSED : value === false ? BrowserQualificationStatus.FAILED : BrowserQualificationStatus.PENDING;
    return Object.freeze({ key, label, status });
  });
  const failed = checks.some((check) => check.status === BrowserQualificationStatus.FAILED);
  const pending = checks.some((check) => check.status === BrowserQualificationStatus.PENDING);
  return Object.freeze({
    status: failed ? BrowserQualificationStatus.FAILED : pending ? BrowserQualificationStatus.PENDING : BrowserQualificationStatus.PASSED,
    checks: Object.freeze(checks),
  });
}
