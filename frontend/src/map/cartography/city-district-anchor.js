/** P006.7.11.15.9.2 - governed CITY_DISTRICT label adapters. */
import {
  CartographicAnchorKind,
  CartographicLabelClass,
  createCartographicLabelCandidate,
  createPresentationAnchor,
} from "./contracts.js";

const ADMIN_ID = /^NG-ADM-[0-9]{6}$/;

export function isNoveGeoCityDistrictMapItem(item) {
  return Boolean(
    item
    && item.family === "ADMINISTRATIVE_AREA"
    && String(item.classificationCode || "").toUpperCase() === "CITY_DISTRICT"
    && ADMIN_ID.test(String(item.subjectId || ""))
    && ADMIN_ID.test(String(item.parentCityId || ""))
    && String(item.geometryRole || "").toUpperCase() === "ADMINISTRATIVE_BOUNDARY"
    && String(item.partitionStatus || "").toUpperCase() === "COMPLETE"
  );
}

function labelCoordinates(item) {
  const point = item?.labelPoint;
  if (!point || point.type !== "Point" || !Array.isArray(point.coordinates) || point.coordinates.length < 2) {
    throw new TypeError("CITY_DISTRICT map item requires GeoJSON Point labelPoint");
  }
  const longitude = Number(point.coordinates[0]);
  const latitude = Number(point.coordinates[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new TypeError("CITY_DISTRICT labelPoint coordinates must be finite");
  }
  return { longitude, latitude };
}

function runtimeMode(item, readRuntime) {
  if (String(item?.runtimeEffectScope || "").toUpperCase() === "SHARED_REFERENCE") {
    return "shared_reference";
  }
  const runtime = String(readRuntime || "").toLowerCase();
  if (!new Set(["simulation", "production"]).has(runtime)) {
    throw new Error("CITY_DISTRICT label requires simulation or production readRuntime");
  }
  return runtime;
}

export function assertPublishedNoveGeoCityDistrictSubset(items = []) {
  if (!Array.isArray(items)) throw new TypeError("national map items must be an array");
  const districts = items.filter((item) =>
    item?.family === "ADMINISTRATIVE_AREA"
    && String(item?.classificationCode || "").toUpperCase() === "CITY_DISTRICT"
  );
  const seen = new Set();
  for (const item of districts) {
    if (!isNoveGeoCityDistrictMapItem(item)) {
      throw new Error(`invalid governed CITY_DISTRICT map item: ${item?.subjectId || "missing"}`);
    }
    if (seen.has(item.subjectId)) {
      throw new Error(`duplicate CITY_DISTRICT identity: ${item.subjectId}`);
    }
    seen.add(item.subjectId);
  }
  return Object.freeze(
    districts.sort((a, b) => String(a.subjectId).localeCompare(String(b.subjectId)))
  );
}

export function createNoveGeoCityDistrictLabelCandidate(item, { readRuntime } = {}) {
  if (!isNoveGeoCityDistrictMapItem(item)) {
    throw new TypeError("item is not a governed NoveGeo CITY_DISTRICT map item");
  }
  const { longitude, latitude } = labelCoordinates(item);
  const algorithmId = String(item.labelPointAlgorithmId || "").trim();
  const algorithmVersion = Number(item.labelPointAlgorithmVersion);
  if (!algorithmId || !Number.isInteger(algorithmVersion) || algorithmVersion < 1) {
    throw new Error("CITY_DISTRICT label point requires algorithm identity/version");
  }
  if (!item.geometryId || !Number.isInteger(item.geometryVersion) || item.geometryVersion < 1) {
    throw new Error("CITY_DISTRICT label point requires source geometry identity/version");
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
    labelClass: CartographicLabelClass.ADMIN_DISTRICT,
    anchor,
    runtimeMode: runtimeMode(item, readRuntime),
    publicationReference: item.publicationReference,
  });
}

export function createNoveGeoCityDistrictLabelCandidates(items = [], options = {}) {
  const districts = assertPublishedNoveGeoCityDistrictSubset(items);
  return Object.freeze(
    districts
      .map((item) => createNoveGeoCityDistrictLabelCandidate(item, options))
      .sort((a, b) => a.subjectId.localeCompare(b.subjectId))
  );
}
