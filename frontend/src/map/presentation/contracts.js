/** P004.3-P004.4 immutable map presentation contracts. */

export const MAP_VIEWPORT_ID = "viewport:novegeo:primary-map";
export const MAP_VIEWPORT_VERSION = 1;
export const MAP_RENDER_PLAN_ID = "render-plan:novegeo:map-core";
export const MAP_RENDER_PLAN_VERSION = 1;
export const COORDINATE_GRID_ID = "overlay:novegeo:coordinate-grid";
export const EQUATOR_OVERLAY_ID = "overlay:novegeo:equator";

export const MapFitMode = Object.freeze({
  WORLD: "world",
  BOUNDARY: "boundary",
  EXPLICIT_EXTENT: "explicit_extent",
});

export const MapLayer = Object.freeze({
  BACKGROUND: "background",
  GRATICULE: "graticule",
  EQUATOR: "equator",
  BOUNDARY_FILL: "boundary_fill",
  BOUNDARY_STROKE: "boundary_stroke",
  LABELS: "labels",
  DIAGNOSTICS: "diagnostics",
});

export const MAP_LAYER_ORDER = Object.freeze([
  MapLayer.BACKGROUND,
  MapLayer.GRATICULE,
  MapLayer.EQUATOR,
  MapLayer.BOUNDARY_FILL,
  MapLayer.BOUNDARY_STROKE,
  MapLayer.LABELS,
  MapLayer.DIAGNOSTICS,
]);

export function freezeExtent(extent) {
  const normalized = {
    minLongitude: Number(extent?.minLongitude),
    minLatitude: Number(extent?.minLatitude),
    maxLongitude: Number(extent?.maxLongitude),
    maxLatitude: Number(extent?.maxLatitude),
  };
  for (const value of Object.values(normalized)) {
    if (!Number.isFinite(value)) throw new TypeError("map extent values must be finite");
  }
  if (normalized.minLongitude >= normalized.maxLongitude || normalized.minLatitude >= normalized.maxLatitude) {
    throw new RangeError("map extent minimums must be lower than maximums");
  }
  if (normalized.minLongitude < -180 || normalized.maxLongitude > 180 || normalized.minLatitude < -90 || normalized.maxLatitude > 90) {
    throw new RangeError("map extent exceeds the geographic coordinate reference");
  }
  return Object.freeze(normalized);
}
