/** P006.7.11.15.7.3 — governed CITY label adapters for existing cartography contracts. */
import {
  CartographicAnchorKind,
  CartographicLabelClass,
  createCartographicLabelCandidate,
  createPresentationAnchor,
} from "./contracts.js";

export const OFFICIAL_NOVEGEO_CITY_IDS = Object.freeze([
  "NG-ADM-000009",
  "NG-ADM-000032",
  "NG-ADM-000055",
  "NG-ADM-000078",
  "NG-ADM-000101",
  "NG-ADM-000124",
  "NG-ADM-000147",
  "NG-ADM-000170",
]);
const OFFICIAL_CITY_SET = new Set(OFFICIAL_NOVEGEO_CITY_IDS);

export function isNoveGeoCityMapItem(item) {
  return Boolean(
    item
    && item.family === "ADMINISTRATIVE_AREA"
    && String(item.classificationCode || "").toUpperCase() === "CITY"
    && OFFICIAL_CITY_SET.has(String(item.subjectId || ""))
  );
}

function labelCoordinates(item) {
  const point = item?.labelPoint;
  if (!point || point.type !== "Point" || !Array.isArray(point.coordinates) || point.coordinates.length < 2) {
    throw new TypeError("CITY map item requires GeoJSON Point labelPoint");
  }
  const longitude = Number(point.coordinates[0]);
  const latitude = Number(point.coordinates[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new TypeError("CITY labelPoint coordinates must be finite");
  }
  return { longitude, latitude };
}

function runtimeMode(item, readRuntime) {
  if (String(item?.runtimeEffectScope || "").toUpperCase() === "SHARED_REFERENCE") return "shared_reference";
  const runtime = String(readRuntime || "").toLowerCase();
  if (!new Set(["simulation", "production"]).has(runtime)) {
    throw new Error("CITY label requires simulation or production readRuntime");
  }
  return runtime;
}

export function createNoveGeoCityLabelCandidate(item, { readRuntime } = {}) {
  if (!isNoveGeoCityMapItem(item)) throw new TypeError("item is not an official NoveGeo CITY map item");
  if (!String(item.parentRegionId || "").startsWith("NG-ADM-")) {
    throw new Error("CITY map item requires parentRegionId");
  }
  const { longitude, latitude } = labelCoordinates(item);
  const algorithmId = String(item.labelPointAlgorithmId || "").trim();
  const algorithmVersion = Number(item.labelPointAlgorithmVersion);
  if (!algorithmId || !Number.isInteger(algorithmVersion) || algorithmVersion < 1) {
    throw new Error("CITY label point requires algorithm identity/version");
  }
  if (!item.geometryId || !Number.isInteger(item.geometryVersion) || item.geometryVersion < 1) {
    throw new Error("CITY label point requires source geometry identity/version");
  }

  const anchor = createPresentationAnchor({
    kind: CartographicAnchorKind.DERIVED_PRESENTATION,
    longitude,
    latitude,
    sourceGeometryId: item.geometryId,
    sourceGeometryVersion: item.geometryVersion,
    algorithmId,
    algorithmVersion,
  });
  return createCartographicLabelCandidate({
    subjectId: item.subjectId,
    displayName: item.displayName,
    labelClass: CartographicLabelClass.ADMIN_CITY,
    anchor,
    runtimeMode: runtimeMode(item, readRuntime),
    publicationReference: item.publicationReference,
  });
}

export function createNoveGeoCityLabelCandidates(items = [], options = {}) {
  const cities = assertPublishedNoveGeoCitySubset(items);
  return Object.freeze(
    cities
      .map((item) => createNoveGeoCityLabelCandidate(item, options))
      .sort((a, b) => a.subjectId.localeCompare(b.subjectId))
  );
}

export function assertPublishedNoveGeoCitySubset(items = []) {
  if (!Array.isArray(items)) throw new TypeError("national map items must be an array");
  const classifiedCities = items.filter((item) =>
    item?.family === "ADMINISTRATIVE_AREA"
    && String(item?.classificationCode || "").toUpperCase() === "CITY"
  );
  const seen = new Set();
  for (const item of classifiedCities) {
    const id = String(item?.subjectId || "");
    if (!OFFICIAL_CITY_SET.has(id)) {
      throw new Error(`official NoveGeo CITY subset contains unknown identity: ${id || "missing"}`);
    }
    if (seen.has(id)) {
      throw new Error(`official NoveGeo CITY subset contains duplicate identity: ${id}`);
    }
    seen.add(id);
  }
  return Object.freeze(classifiedCities.sort((a, b) => String(a.subjectId).localeCompare(String(b.subjectId))));
}
