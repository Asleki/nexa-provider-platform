/** P006.1 immutable NoveGeo map-navigation state. */
export const MAP_NAVIGATION_STATE_ID = "state:novegeo:map-navigation";
export const MAP_NAVIGATION_STATE_VERSION = 1;
export const MIN_ZOOM = 1;
export const MAX_ZOOM = 8;

function finite(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${label} must be finite`);
  return number;
}

export function clampZoom(value) {
  return Math.min(MAX_ZOOM, Math.max(MIN_ZOOM, finite(value, "zoom")));
}

export function createNavigationState({ zoom = 1, offsetX = 0, offsetY = 0, revision = 0, source = "initial" } = {}) {
  const normalizedRevision = Number(revision);
  if (!Number.isInteger(normalizedRevision) || normalizedRevision < 0) throw new RangeError("navigation revision must be a non-negative integer");
  return Object.freeze({
    stateId: MAP_NAVIGATION_STATE_ID,
    stateVersion: MAP_NAVIGATION_STATE_VERSION,
    viewportStateVersion: 1,
    zoom: clampZoom(zoom),
    offsetX: finite(offsetX, "offsetX"),
    offsetY: finite(offsetY, "offsetY"),
    revision: normalizedRevision,
    source: String(source || "unknown"),
    runtimeMode: "shared_reference",
  });
}

export function constrainOffsets({ zoom, offsetX, offsetY }, { width, height }) {
  const z = clampZoom(zoom);
  const w = Math.max(1, finite(width, "width"));
  const h = Math.max(1, finite(height, "height"));
  const maxX = ((z - 1) * w) / 2;
  const maxY = ((z - 1) * h) / 2;
  const constrainedX = Math.max(-maxX, Math.min(maxX, finite(offsetX, "offsetX")));
  const constrainedY = Math.max(-maxY, Math.min(maxY, finite(offsetY, "offsetY")));
  return Object.freeze({
    offsetX: Object.is(constrainedX, -0) ? 0 : constrainedX,
    offsetY: Object.is(constrainedY, -0) ? 0 : constrainedY,
  });
}
