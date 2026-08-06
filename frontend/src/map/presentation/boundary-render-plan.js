/** Deterministic MultiPolygon-to-path render-plan generation. */
import { validateWorldBoundaryPublication } from "../geography/contracts.js";
import { geographicToViewport } from "./viewport.js";
import { MAP_RENDER_PLAN_ID, MAP_RENDER_PLAN_VERSION } from "./contracts.js";

function validatePosition(position) {
  if (!Array.isArray(position) || position.length < 2) throw new TypeError("boundary position must contain longitude and latitude");
  return position;
}

export function createBoundaryRenderPlan(publication, viewport) {
  const validated = validateWorldBoundaryPublication(publication);
  const polygons = validated.geometry.coordinates.map((polygon, polygonIndex) => {
    if (!Array.isArray(polygon) || polygon.length === 0) throw new Error("boundary polygon must contain at least one ring");
    const rings = polygon.map((ring, ringIndex) => {
      if (!Array.isArray(ring) || ring.length < 4) throw new Error("boundary ring must contain at least four positions");
      const points = ring.map((position) => {
        const [longitude, latitude] = validatePosition(position);
        return geographicToViewport(longitude, latitude, viewport);
      });
      return Object.freeze({ polygonIndex, ringIndex, isExterior: ringIndex === 0, points: Object.freeze(points) });
    });
    return Object.freeze({ polygonIndex, rings: Object.freeze(rings) });
  });
  return Object.freeze({
    renderPlanId: MAP_RENDER_PLAN_ID,
    renderPlanVersion: MAP_RENDER_PLAN_VERSION,
    publicationId: validated.publicationId,
    boundaryId: validated.boundaryId,
    boundaryVersion: validated.boundaryVersion,
    viewportId: viewport.viewportId,
    viewportVersion: viewport.viewportVersion,
    polygons: Object.freeze(polygons),
  });
}
