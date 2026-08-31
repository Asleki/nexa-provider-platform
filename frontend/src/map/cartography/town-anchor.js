/** P006.7.11.15.9.3 - governed TOWN label adapters. */
import {
  CartographicAnchorKind,
  CartographicLabelClass,
  createCartographicLabelCandidate,
  createPresentationAnchor,
} from "./contracts.js";

const PLACE_ID = /^NG-PLC-[0-9]{6}$/;

export function isNoveGeoTownMapItem(item) {
  const parent = item?.parentPlaceId;
  return Boolean(
    item
    && item.family === "PLACE"
    && String(item.classificationCode || "").toUpperCase() === "TOWN"
    && PLACE_ID.test(String(item.subjectId || ""))
    && (parent === null || parent === undefined || PLACE_ID.test(String(parent)))
    && String(item.geometryRole || "").toUpperCase() === "SETTLEMENT_FOOTPRINT"
  );
}

function labelCoordinates(item) {
  const point = item?.labelPoint;
  if (!point || point.type !== "Point" || !Array.isArray(point.coordinates) || point.coordinates.length < 2) {
    throw new TypeError("TOWN map item requires GeoJSON Point labelPoint");
  }
  const longitude = Number(point.coordinates[0]);
  const latitude = Number(point.coordinates[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) {
    throw new TypeError("TOWN labelPoint coordinates must be finite");
  }
  return { longitude, latitude };
}

function runtimeMode(item, readRuntime) {
  if (String(item?.runtimeEffectScope || "").toUpperCase() === "SHARED_REFERENCE") {
    return "shared_reference";
  }
  const runtime = String(readRuntime || "").toLowerCase();
  if (!new Set(["simulation", "production"]).has(runtime)) {
    throw new Error("TOWN label requires simulation or production readRuntime");
  }
  return runtime;
}

export function assertPublishedNoveGeoTownSubset(items = []) {
  if (!Array.isArray(items)) throw new TypeError("national map items must be an array");
  const towns = items.filter((item) =>
    item?.family === "PLACE"
    && String(item?.classificationCode || "").toUpperCase() === "TOWN"
  );
  const seen = new Set();
  for (const item of towns) {
    if (!isNoveGeoTownMapItem(item)) {
      throw new Error(`invalid governed TOWN map item: ${item?.subjectId || "missing"}`);
    }
    if (seen.has(item.subjectId)) {
      throw new Error(`duplicate TOWN identity: ${item.subjectId}`);
    }
    seen.add(item.subjectId);
  }
  return Object.freeze(
    towns.sort((a, b) => String(a.subjectId).localeCompare(String(b.subjectId)))
  );
}

export function createNoveGeoTownLabelCandidate(item, { readRuntime } = {}) {
  if (!isNoveGeoTownMapItem(item)) {
    throw new TypeError("item is not a governed NoveGeo TOWN map item");
  }
  const { longitude, latitude } = labelCoordinates(item);
  const algorithmId = String(item.labelPointAlgorithmId || "").trim();
  const algorithmVersion = Number(item.labelPointAlgorithmVersion);
  if (!algorithmId || !Number.isInteger(algorithmVersion) || algorithmVersion < 1) {
    throw new Error("TOWN label point requires algorithm identity/version");
  }
  if (!item.geometryId || !Number.isInteger(item.geometryVersion) || item.geometryVersion < 1) {
    throw new Error("TOWN label point requires source geometry identity/version");
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
    labelClass: CartographicLabelClass.TOWN,
    anchor,
    runtimeMode: runtimeMode(item, readRuntime),
    publicationReference: item.publicationReference,
  });
}

export function createNoveGeoTownLabelCandidates(items = [], options = {}) {
  const towns = assertPublishedNoveGeoTownSubset(items);
  return Object.freeze(
    towns
      .map((item) => createNoveGeoTownLabelCandidate(item, options))
      .sort((a, b) => a.subjectId.localeCompare(b.subjectId))
  );
}
