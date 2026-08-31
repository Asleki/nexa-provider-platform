/** P006.7.11.15.9.1 - governed MUNICIPALITY label adapters. */
import {
  CartographicAnchorKind,
  CartographicLabelClass,
  createCartographicLabelCandidate,
  createPresentationAnchor,
} from "./contracts.js";

export const MUNICIPALITY_TARGET_COUNT = 24;

export function isNoveGeoMunicipalityMapItem(item) {
  return Boolean(
    item
    && item.family === "ADMINISTRATIVE_AREA"
    && String(item.classificationCode || "").toUpperCase() === "MUNICIPALITY"
    && /^NG-ADM-[0-9]{6}$/.test(String(item.subjectId || ""))
    && /^NG-ADM-[0-9]{6}$/.test(String(item.parentRegionId || ""))
  );
}

function labelCoordinates(item) {
  const point = item?.labelPoint;
  if (!point || point.type !== "Point" || !Array.isArray(point.coordinates) || point.coordinates.length < 2) {
    throw new TypeError("MUNICIPALITY map item requires GeoJSON Point labelPoint");
  }
  const longitude = Number(point.coordinates[0]);
  const latitude = Number(point.coordinates[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new TypeError("MUNICIPALITY labelPoint coordinates must be finite");
  }
  return { longitude, latitude };
}

function runtimeMode(item, readRuntime) {
  if (String(item?.runtimeEffectScope || "").toUpperCase() === "SHARED_REFERENCE") {
    return "shared_reference";
  }
  const runtime = String(readRuntime || "").toLowerCase();
  if (!new Set(["simulation", "production"]).has(runtime)) {
    throw new Error("MUNICIPALITY label requires simulation or production readRuntime");
  }
  return runtime;
}

export function assertPublishedNoveGeoMunicipalitySubset(items = []) {
  if (!Array.isArray(items)) throw new TypeError("national map items must be an array");
  const municipalities = items.filter((item) =>
    item?.family === "ADMINISTRATIVE_AREA"
    && String(item?.classificationCode || "").toUpperCase() === "MUNICIPALITY"
  );
  if (municipalities.length > MUNICIPALITY_TARGET_COUNT) {
    throw new Error("published MUNICIPALITY subset exceeds governed target count");
  }
  const seen = new Set();
  for (const item of municipalities) {
    if (!isNoveGeoMunicipalityMapItem(item)) {
      throw new Error(`invalid governed MUNICIPALITY map item: ${item?.subjectId || "missing"}`);
    }
    if (seen.has(item.subjectId)) {
      throw new Error(`duplicate MUNICIPALITY identity: ${item.subjectId}`);
    }
    seen.add(item.subjectId);
  }
  return Object.freeze(
    municipalities.sort((a, b) => String(a.subjectId).localeCompare(String(b.subjectId)))
  );
}

export function createNoveGeoMunicipalityLabelCandidate(item, { readRuntime } = {}) {
  if (!isNoveGeoMunicipalityMapItem(item)) {
    throw new TypeError("item is not a governed NoveGeo MUNICIPALITY map item");
  }
  const { longitude, latitude } = labelCoordinates(item);
  const algorithmId = String(item.labelPointAlgorithmId || "").trim();
  const algorithmVersion = Number(item.labelPointAlgorithmVersion);
  if (!algorithmId || !Number.isInteger(algorithmVersion) || algorithmVersion < 1) {
    throw new Error("MUNICIPALITY label point requires algorithm identity/version");
  }
  if (!item.geometryId || !Number.isInteger(item.geometryVersion) || item.geometryVersion < 1) {
    throw new Error("MUNICIPALITY label point requires source geometry identity/version");
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
    labelClass: CartographicLabelClass.ADMIN_MUNICIPAL,
    anchor,
    runtimeMode: runtimeMode(item, readRuntime),
    publicationReference: item.publicationReference,
  });
}

export function createNoveGeoMunicipalityLabelCandidates(items = [], options = {}) {
  const municipalities = assertPublishedNoveGeoMunicipalitySubset(items);
  return Object.freeze(
    municipalities
      .map((item) => createNoveGeoMunicipalityLabelCandidate(item, options))
      .sort((a, b) => a.subjectId.localeCompare(b.subjectId))
  );
}
