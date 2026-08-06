/** Declared-versus-derived world extent qualification. */
import { freezeExtent } from "../presentation/contracts.js";
import { MAP_VALIDATION_TOLERANCE } from "./contracts.js";

function nearlyEqual(left, right, tolerance) {
  return Math.abs(left - right) <= tolerance;
}

export function validateExtentParity(declaredExtent, derivedExtent, tolerance = MAP_VALIDATION_TOLERANCE) {
  const declared = freezeExtent(declaredExtent);
  const derived = freezeExtent(derivedExtent);
  const fields = ["minLongitude", "minLatitude", "maxLongitude", "maxLatitude"];
  const mismatches = fields.filter((field) => !nearlyEqual(declared[field], derived[field], tolerance));
  if (mismatches.length > 0) {
    throw new Error(`declared boundary extent does not match derived geometry extent: ${mismatches.join(", ")}`);
  }
  return Object.freeze({ declared, derived, tolerance, matched: true });
}

export function assertPositionsWithinExtent(positions, extent, tolerance = MAP_VALIDATION_TOLERANCE) {
  const validatedExtent = freezeExtent(extent);
  for (const [longitude, latitude] of positions) {
    if (
      longitude < validatedExtent.minLongitude - tolerance ||
      longitude > validatedExtent.maxLongitude + tolerance ||
      latitude < validatedExtent.minLatitude - tolerance ||
      latitude > validatedExtent.maxLatitude + tolerance
    ) {
      throw new RangeError("boundary position falls outside the declared extent");
    }
  }
  return validatedExtent;
}
