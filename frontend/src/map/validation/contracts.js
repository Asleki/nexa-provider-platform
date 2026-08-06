/** P004.5 immutable map-core qualification contracts. */

export const MAP_QUALIFICATION_ID = "qualification:novegeo:map-core";
export const MAP_QUALIFICATION_VERSION = 1;
export const MAP_VALIDATION_TOLERANCE = 1e-8;

export const ValidationSeverity = Object.freeze({
  INFO: "INFO",
  ERROR: "ERROR",
});

export const QualificationStatus = Object.freeze({
  PASSED: "PASSED",
  FAILED: "FAILED",
});

export function createValidationFinding({ code, passed, message, details = {} }) {
  const normalizedCode = String(code || "").trim();
  const normalizedMessage = String(message || "").trim();
  if (!normalizedCode) throw new TypeError("validation finding code is required");
  if (!normalizedMessage) throw new TypeError("validation finding message is required");
  if (!details || typeof details !== "object" || Array.isArray(details)) {
    throw new TypeError("validation finding details must be an object");
  }
  return Object.freeze({
    code: normalizedCode,
    passed: Boolean(passed),
    severity: passed ? ValidationSeverity.INFO : ValidationSeverity.ERROR,
    message: normalizedMessage,
    details: Object.freeze({ ...details }),
  });
}
