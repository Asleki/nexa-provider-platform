/**
 * NexiLabs NoveGeo PWA
 * P002.1/P002.2 — Public runtime configuration contract.
 */

export const RuntimeMode = Object.freeze({
  DEVELOPMENT: "development",
  TESTING: "testing",
  SIMULATION: "simulation",
  STAGING: "staging",
  PRODUCTION: "production",
});

const RUNTIME_VALUES = Object.freeze(Object.values(RuntimeMode));
const FORBIDDEN_VALUE_PATTERNS = Object.freeze([
  /postgres(?:ql)?:\/\//i,
  /\.rds\.amazonaws\.com/i,
  /(?:^|[^0-9])5432(?:[^0-9]|$)/,
  /aws[_-]?(?:access|secret)[_-]?key/i,
  /database[_-]?password/i,
  /session[_-]?token/i,
]);

function assertPlainObject(value, label) {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    throw new TypeError(`${label} must be an object`);
  }
}

function assertSafePublicValue(value, path) {
  if (value === null || value === undefined) return;
  if (typeof value === "object") {
    assertPlainObject(value, path);
    for (const [key, child] of Object.entries(value)) {
      assertSafePublicValue(child, `${path}.${key}`);
    }
    return;
  }
  const text = String(value);
  for (const pattern of FORBIDDEN_VALUE_PATTERNS) {
    if (pattern.test(text)) {
      throw new Error(`Unsafe public runtime configuration at ${path}`);
    }
  }
}

function normalizeApiBaseUrl(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  const parsed = new URL(text);
  if (parsed.protocol !== "https:" && parsed.hostname !== "localhost") {
    throw new Error("apiBaseUrl must use HTTPS outside localhost");
  }
  return parsed.toString().replace(/\/$/, "");
}

export function createRuntimeConfig(input = {}) {
  assertPlainObject(input, "runtime configuration");
  assertSafePublicValue(input, "runtime");

  const runtimeMode = String(input.runtimeMode ?? RuntimeMode.DEVELOPMENT).trim();
  if (!RUNTIME_VALUES.includes(runtimeMode)) {
    throw new Error(`Unsupported runtime mode: ${runtimeMode}`);
  }

  const config = {
    applicationId: "nexilabs-novegeo-pwa",
    applicationName: "NexiLabs NoveGeo PWA",
    applicationVersion: String(input.applicationVersion ?? "0.1.0").trim(),
    runtimeMode,
    environmentName: String(input.environmentName ?? runtimeMode).trim(),
    apiBaseUrl: normalizeApiBaseUrl(input.apiBaseUrl),
    buildReference: String(input.buildReference ?? "local-development").trim(),
    capabilities: Object.freeze([
      "application_shell",
      "runtime_configuration",
      "health_state",
      "governed_world_boundary",
      "coordinate_reference",
      "coordinate_projection",
    ]),
  };

  if (!config.applicationVersion || !config.environmentName || !config.buildReference) {
    throw new Error("applicationVersion, environmentName and buildReference are required");
  }
  return Object.freeze(config);
}
