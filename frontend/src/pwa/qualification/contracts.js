/** P003.5 — Stable contracts for install and offline qualification evidence. */
export const QualificationStatus = Object.freeze({ PASSED: "PASSED", FAILED: "FAILED" });
export const FindingSeverity = Object.freeze({ INFO: "INFO", ERROR: "ERROR" });

export function createFinding({ code, passed, message, details = {} }) {
  if (!/^[A-Z0-9_]+$/.test(code)) throw new TypeError("finding code must be uppercase snake case");
  if (typeof passed !== "boolean") throw new TypeError("finding passed must be boolean");
  return Object.freeze({
    code,
    passed,
    severity: passed ? FindingSeverity.INFO : FindingSeverity.ERROR,
    message: String(message),
    details: Object.freeze({ ...details })
  });
}

export function createQualificationReceipt({ qualificationId, generatedAt, applicationVersion, cacheVersion, fingerprints, findings, manualEvidence }) {
  const frozenFindings = Object.freeze([...findings]);
  const passed = frozenFindings.every((finding) => finding.passed);
  return Object.freeze({
    qualificationId,
    milestoneId: "P003.5",
    generatedAt,
    applicationVersion,
    cacheVersion,
    status: passed ? QualificationStatus.PASSED : QualificationStatus.FAILED,
    fingerprints: Object.freeze({ ...fingerprints }),
    findings: frozenFindings,
    manualEvidence: Object.freeze({ ...manualEvidence }),
    databaseWritesPerformed: 0
  });
}
