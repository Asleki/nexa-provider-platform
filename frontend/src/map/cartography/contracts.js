/** P006.7.11.15.4 — immutable cartographic presentation contracts. */

export const CARTOGRAPHY_ID = "cartography:novegeo:national-map";
export const CARTOGRAPHY_VERSION = 1;

export const CartographicLabelClass = Object.freeze({
  COUNTRY: "COUNTRY",
  ADMIN_REGION: "ADMIN_REGION",
  ADMIN_DISTRICT: "ADMIN_DISTRICT",
  ADMIN_MUNICIPAL: "ADMIN_MUNICIPAL",
  ADMIN_CITY: "ADMIN_CITY",
  CITY: "CITY",
  TOWN: "TOWN",
  VILLAGE: "VILLAGE",
  LOCALITY: "LOCALITY",
  ROAD_ROUTE: "ROAD_ROUTE",
  ROAD_NAME: "ROAD_NAME",
  HYDROLOGY: "HYDROLOGY",
  LANDFORM: "LANDFORM",
});

export const CartographicAnchorKind = Object.freeze({
  DERIVED_PRESENTATION: "DERIVED_PRESENTATION",
  FEATURE_POINT: "FEATURE_POINT",
  FEATURE_CENTROID: "FEATURE_CENTROID",
  FEATURE_LINE: "FEATURE_LINE",
});

const RUNTIME_MODES = new Set(["simulation", "production", "shared_reference"]);

function requiredText(value, name) {
  const normalized = String(value ?? "").trim();
  if (!normalized) throw new TypeError(`${name} is required`);
  return normalized;
}

function finiteCoordinate(value, name, min, max) {
  const number = Number(value);
  if (!Number.isFinite(number) || number < min || number > max) {
    throw new RangeError(`${name} must be between ${min} and ${max}`);
  }
  return number;
}

export function createPresentationAnchor({
  kind = CartographicAnchorKind.DERIVED_PRESENTATION,
  longitude,
  latitude,
  sourceBoundaryId = null,
  sourceBoundaryVersion = null,
  sourceGeometryId = null,
  sourceGeometryVersion = null,
  algorithmId = null,
  algorithmVersion = null,
} = {}) {
  if (!Object.values(CartographicAnchorKind).includes(kind)) {
    throw new Error(`unsupported cartographic anchor kind: ${kind}`);
  }
  const anchor = {
    kind,
    longitude: finiteCoordinate(longitude, "longitude", -180, 180),
    latitude: finiteCoordinate(latitude, "latitude", -90, 90),
    sourceBoundaryId: sourceBoundaryId ? requiredText(sourceBoundaryId, "sourceBoundaryId") : null,
    sourceBoundaryVersion: sourceBoundaryVersion === null ? null : Number(sourceBoundaryVersion),
    sourceGeometryId: sourceGeometryId ? requiredText(sourceGeometryId, "sourceGeometryId") : null,
    sourceGeometryVersion: sourceGeometryVersion === null ? null : Number(sourceGeometryVersion),
    algorithmId: algorithmId ? requiredText(algorithmId, "algorithmId") : null,
    algorithmVersion: algorithmVersion === null ? null : Number(algorithmVersion),
  };
  for (const [idKey, versionKey] of [["sourceBoundaryId", "sourceBoundaryVersion"], ["sourceGeometryId", "sourceGeometryVersion"], ["algorithmId", "algorithmVersion"]]) {
    const id = anchor[idKey];
    const version = anchor[versionKey];
    if ((id === null) !== (version === null)) throw new Error(`${idKey} and ${versionKey} must be supplied together`);
    if (version !== null && (!Number.isInteger(version) || version < 1)) throw new RangeError(`${versionKey} must be a positive integer`);
  }
  if (kind === CartographicAnchorKind.DERIVED_PRESENTATION && !anchor.algorithmId) {
    throw new Error("derived presentation anchors require an algorithm identity/version");
  }
  return Object.freeze(anchor);
}

export function createCartographicLabelCandidate({
  subjectId,
  displayName,
  labelClass,
  anchor,
  runtimeMode = "shared_reference",
  publicationReference = null,
  labelGroupReference = null,
} = {}) {
  const normalizedClass = requiredText(labelClass, "labelClass").toUpperCase();
  if (!Object.values(CartographicLabelClass).includes(normalizedClass)) {
    throw new Error(`unsupported cartographic label class: ${normalizedClass}`);
  }
  const runtime = requiredText(runtimeMode, "runtimeMode").toLowerCase();
  if (!RUNTIME_MODES.has(runtime)) throw new Error(`unsupported cartographic runtime mode: ${runtime}`);
  if (!anchor || typeof anchor !== "object") throw new TypeError("anchor is required");
  return Object.freeze({
    cartographyId: CARTOGRAPHY_ID,
    cartographyVersion: CARTOGRAPHY_VERSION,
    subjectId: requiredText(subjectId, "subjectId"),
    displayName: requiredText(displayName, "displayName"),
    labelClass: normalizedClass,
    anchor,
    runtimeMode: runtime,
    publicationReference: publicationReference ? requiredText(publicationReference, "publicationReference") : null,
    labelGroupReference: labelGroupReference ? requiredText(labelGroupReference, "labelGroupReference") : null,
  });
}
