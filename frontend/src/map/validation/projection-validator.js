/** Forward/inverse projection qualification for every governed position. */
import { projectCoordinate, unprojectCoordinate, PROJECTION_ID, PROJECTION_VERSION, PROJECTION_TOLERANCE } from "../geography/projection.js";

export function validateProjectionPositions(positions, tolerance = PROJECTION_TOLERANCE) {
  let projectedCount = 0;
  for (const [longitude, latitude] of positions) {
    const projected = projectCoordinate(longitude, latitude);
    if (projected.projectionId !== PROJECTION_ID || projected.projectionVersion !== PROJECTION_VERSION) {
      throw new Error("projection identity or version mismatch");
    }
    if (projected.x < 0 || projected.x > 1 || projected.y < 0 || projected.y > 1) {
      throw new RangeError("projected boundary position falls outside normalized world bounds");
    }
    const restored = unprojectCoordinate(projected);
    if (Math.abs(restored.longitude - longitude) > tolerance || Math.abs(restored.latitude - latitude) > tolerance) {
      throw new Error("projection round trip exceeded the approved tolerance");
    }
    projectedCount += 1;
  }
  return Object.freeze({ projectedCount, projectionId: PROJECTION_ID, projectionVersion: PROJECTION_VERSION, tolerance });
}
