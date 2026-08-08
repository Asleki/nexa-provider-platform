/** P006.5 — versioned dynamic world-state envelope consumed by the map, never authoritative geography. */
export const NOVEGEO_WORLD_STATE_ID = "state:novegeo:world";
export const NOVEGEO_WORLD_STATE_VERSION = 1;

function nonNegativeInteger(value, label) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0) throw new RangeError(`${label} must be a non-negative integer`);
  return number;
}

function requiredText(value, label) {
  const text = String(value ?? "").trim();
  if (!text) throw new TypeError(`${label} is required`);
  return text;
}

function normalizeEffectiveAt(value) {
  if (value === null || value === undefined || value === "") return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) throw new TypeError("effectiveAt must be a valid timestamp");
  return date.toISOString();
}

function normalizeReference(reference) {
  if (!reference || typeof reference !== "object" || Array.isArray(reference)) throw new TypeError("state reference must be an object");
  const value = reference.value;
  if (!["string", "number", "boolean"].includes(typeof value) && value !== null) throw new TypeError("state reference value must be a primitive or null");
  return Object.freeze({
    stateReferenceId: requiredText(reference.stateReferenceId, "stateReferenceId"),
    subjectReference: requiredText(reference.subjectReference, "subjectReference"),
    stateType: requiredText(reference.stateType, "stateType"),
    value,
  });
}

export function createWorldStateEnvelope({
  revision = 0,
  runtimeMode,
  effectiveAt = null,
  sourceReference = "source:nexilabs:unassigned",
  stateReferences = [],
} = {}) {
  if (!Array.isArray(stateReferences)) throw new TypeError("stateReferences must be an array");
  const normalizedReferences = Object.freeze(stateReferences.map(normalizeReference));
  const ids = new Set(normalizedReferences.map((entry) => entry.stateReferenceId));
  if (ids.size !== normalizedReferences.length) throw new Error("stateReferenceId values must be unique within one world-state revision");
  return Object.freeze({
    worldStateId: NOVEGEO_WORLD_STATE_ID,
    worldStateVersion: NOVEGEO_WORLD_STATE_VERSION,
    revision: nonNegativeInteger(revision, "world-state revision"),
    runtimeMode: requiredText(runtimeMode, "runtimeMode"),
    effectiveAt: normalizeEffectiveAt(effectiveAt),
    sourceReference: requiredText(sourceReference, "sourceReference"),
    stateReferences: normalizedReferences,
    mutatesGovernedGeography: false,
  });
}

export function validateWorldStateEnvelope(value, { runtimeMode } = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("world-state update must be an object");
  if (value.worldStateId !== NOVEGEO_WORLD_STATE_ID) throw new Error("unsupported world-state identity");
  if (value.worldStateVersion !== NOVEGEO_WORLD_STATE_VERSION) throw new Error("unsupported world-state version");
  const normalized = createWorldStateEnvelope(value);
  if (runtimeMode !== undefined && normalized.runtimeMode !== String(runtimeMode)) throw new Error("world-state update belongs to a different runtime mode");
  if (value.mutatesGovernedGeography === true) throw new Error("world-state updates may not mutate governed geography");
  return normalized;
}
