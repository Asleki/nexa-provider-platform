/** Versioned equirectangular world projection matching the Python reference. */
import { createGeographicCoordinate } from "./contracts.js";

export const PROJECTION_ID = "projection:novegeo:equirectangular-world";
export const PROJECTION_VERSION = 1;
export const PROJECTION_TOLERANCE = 1e-8;

export function projectCoordinate(longitude, latitude) {
  const coordinate = createGeographicCoordinate(longitude, latitude);
  return Object.freeze({
    x: (coordinate.longitude + 180) / 360,
    y: (90 - coordinate.latitude) / 180,
    projectionId: PROJECTION_ID,
    projectionVersion: PROJECTION_VERSION,
  });
}

export function unprojectCoordinate(projected) {
  if (!projected || projected.projectionId !== PROJECTION_ID || projected.projectionVersion !== PROJECTION_VERSION) {
    throw new Error("projected coordinate uses an incompatible projection contract");
  }
  const x = Number(projected.x);
  const y = Number(projected.y);
  if (!Number.isFinite(x) || !Number.isFinite(y) || x < 0 || x > 1 || y < 0 || y > 1) {
    throw new RangeError("normalized projected coordinates must be between zero and one");
  }
  return createGeographicCoordinate(x * 360 - 180, 90 - y * 180);
}
