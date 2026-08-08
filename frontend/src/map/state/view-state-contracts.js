/** P006.4 — immutable, runtime-scoped NoveGeo map view-state contract. */
import { MAP_LAYER_CATALOG, createLayerVisibility } from "../controls/layer-state.js";

export const MAP_VIEW_STATE_ID = "state:novegeo:map-view";
export const MAP_VIEW_STATE_VERSION = 1;

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

function nonNegativeInteger(value, label) {
  const number = Number(value);
  if (!Number.isInteger(number) || number < 0) throw new RangeError(`${label} must be a non-negative integer`);
  return number;
}

function normalizeRuntimeMode(value) {
  const text = String(value ?? "").trim();
  if (!text) throw new TypeError("runtimeMode is required");
  return text;
}

function normalizeNavigation(navigation = {}) {
  return Object.freeze({
    zoom: finite(navigation.zoom ?? 1, "navigation.zoom"),
    offsetX: finite(navigation.offsetX ?? 0, "navigation.offsetX"),
    offsetY: finite(navigation.offsetY ?? 0, "navigation.offsetY"),
  });
}

function normalizeSelection(selection) {
  if (!selection) return null;
  const coordinate = selection.selectedCoordinate ?? selection.coordinate ?? selection;
  return Object.freeze({
    longitude: finite(coordinate.longitude, "selection.longitude"),
    latitude: finite(coordinate.latitude, "selection.latitude"),
    source: String(selection.source ?? "recovered_view_state"),
  });
}

export function createMapViewState({
  revision = 0,
  runtimeMode,
  navigation,
  layerVisibility,
  selection = null,
} = {}) {
  const visibility = createLayerVisibility(layerVisibility ?? {});
  const normalizedVisibility = Object.freeze(Object.fromEntries(
    MAP_LAYER_CATALOG.map(({ key }) => [key, visibility[key] !== false]),
  ));

  return Object.freeze({
    viewStateId: MAP_VIEW_STATE_ID,
    viewStateVersion: MAP_VIEW_STATE_VERSION,
    revision: nonNegativeInteger(revision, "view-state revision"),
    runtimeMode: normalizeRuntimeMode(runtimeMode),
    navigation: normalizeNavigation(navigation),
    layerVisibility: normalizedVisibility,
    selection: normalizeSelection(selection),
  });
}

export function validateMapViewState(value, { runtimeMode } = {}) {
  if (!value || typeof value !== "object" || Array.isArray(value)) throw new TypeError("map view state must be an object");
  if (value.viewStateId !== MAP_VIEW_STATE_ID) throw new Error("unsupported map view-state identity");
  if (value.viewStateVersion !== MAP_VIEW_STATE_VERSION) throw new Error("unsupported map view-state version");
  const normalized = createMapViewState(value);
  if (runtimeMode !== undefined && normalized.runtimeMode !== String(runtimeMode)) throw new Error("map view state belongs to a different runtime mode");
  return normalized;
}
