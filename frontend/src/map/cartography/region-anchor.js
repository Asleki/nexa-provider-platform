/** P006.7.11.15.6.2 — governed REGION label adapters for existing cartography contracts. */
import {
  CartographicAnchorKind,
  CartographicLabelClass,
  createCartographicLabelCandidate,
  createPresentationAnchor,
} from "./contracts.js";

export const OFFICIAL_NOVEGEO_REGION_IDS = Object.freeze([
  "NG-ADM-000001",
  "NG-ADM-000002",
  "NG-ADM-000003",
  "NG-ADM-000004",
  "NG-ADM-000005",
  "NG-ADM-000006",
  "NG-ADM-000007",
  "NG-ADM-000008",
]);
const OFFICIAL_REGION_SET = new Set(OFFICIAL_NOVEGEO_REGION_IDS);

export function isNoveGeoRegionMapItem(item) {
  return Boolean(
    item
    && item.family === "ADMINISTRATIVE_AREA"
    && String(item.classificationCode || "").toUpperCase() === "REGION"
    && OFFICIAL_REGION_SET.has(String(item.subjectId || ""))
  );
}

function labelCoordinates(item) {
  const point = item?.labelPoint;
  if (!point || point.type !== "Point" || !Array.isArray(point.coordinates) || point.coordinates.length < 2) {
    throw new TypeError("REGION map item requires GeoJSON Point labelPoint");
  }
  const longitude = Number(point.coordinates[0]);
  const latitude = Number(point.coordinates[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new TypeError("REGION labelPoint coordinates must be finite");
  }
  return { longitude, latitude };
}

function runtimeMode(item, readRuntime) {
  if (String(item?.runtimeEffectScope || "").toUpperCase() === "SHARED_REFERENCE") return "shared_reference";
  const runtime = String(readRuntime || "").toLowerCase();
  if (!new Set(["simulation", "production"]).has(runtime)) {
    throw new Error("REGION label requires simulation or production readRuntime");
  }
  return runtime;
}

export function createNoveGeoRegionLabelCandidate(item, { readRuntime } = {}) {
  if (!isNoveGeoRegionMapItem(item)) throw new TypeError("item is not an official NoveGeo REGION map item");
  const { longitude, latitude } = labelCoordinates(item);
  const algorithmId = String(item.labelPointAlgorithmId || "").trim();
  const algorithmVersion = Number(item.labelPointAlgorithmVersion);
  if (!algorithmId || !Number.isInteger(algorithmVersion) || algorithmVersion < 1) {
    throw new Error("REGION label point requires algorithm identity/version");
  }
  if (!item.geometryId || !Number.isInteger(item.geometryVersion) || item.geometryVersion < 1) {
    throw new Error("REGION label point requires source geometry identity/version");
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
    labelClass: CartographicLabelClass.ADMIN_REGION,
    anchor,
    runtimeMode: runtimeMode(item, readRuntime),
    publicationReference: item.publicationReference,
  });
}

export function createNoveGeoRegionLabelCandidates(items = [], options = {}) {
  if (!Array.isArray(items)) throw new TypeError("REGION map items must be an array");
  return Object.freeze(
    items
      .filter(isNoveGeoRegionMapItem)
      .map((item) => createNoveGeoRegionLabelCandidate(item, options))
      .sort((a, b) => a.subjectId.localeCompare(b.subjectId))
  );
}

export function assertOfficialNoveGeoRegionSet(items = []) {
  if (!Array.isArray(items)) throw new TypeError("national map items must be an array");
  const classifiedRegions = items.filter((item) =>
    item?.family === "ADMINISTRATIVE_AREA"
    && String(item?.classificationCode || "").toUpperCase() === "REGION"
  );
  const ids = classifiedRegions.map((item) => String(item.subjectId || "")).sort();
  const expected = [...OFFICIAL_NOVEGEO_REGION_IDS].sort();
  const uniqueIds = [...new Set(ids)];
  if (classifiedRegions.length !== expected.length
      || uniqueIds.length !== expected.length
      || uniqueIds.some((value, index) => value !== expected[index])) {
    throw new Error(`official NoveGeo REGION set mismatch: expected ${expected.length}, received ${classifiedRegions.length}`);
  }
  return Object.freeze(classifiedRegions.sort((a, b) => a.subjectId.localeCompare(b.subjectId)));
}
