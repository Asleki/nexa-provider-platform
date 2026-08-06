/** Deterministic extent derivation from validated boundary positions. */
import { freezeExtent } from "../presentation/contracts.js";
import { validateBoundaryGeometry } from "./geometry-validator.js";

export function deriveBoundaryExtent(geometry) {
  const validation = validateBoundaryGeometry(geometry);
  let minLongitude = Infinity;
  let minLatitude = Infinity;
  let maxLongitude = -Infinity;
  let maxLatitude = -Infinity;
  for (const [longitude, latitude] of validation.positions) {
    minLongitude = Math.min(minLongitude, longitude);
    minLatitude = Math.min(minLatitude, latitude);
    maxLongitude = Math.max(maxLongitude, longitude);
    maxLatitude = Math.max(maxLatitude, latitude);
  }
  return Object.freeze({
    extent: freezeExtent({ minLongitude, minLatitude, maxLongitude, maxLatitude }),
    polygonCount: validation.polygonCount,
    ringCount: validation.ringCount,
    positionCount: validation.positionCount,
  });
}
