/** Render-plan viewport-bound qualification. */
import { MAP_RENDER_PLAN_ID, MAP_RENDER_PLAN_VERSION, MAP_VIEWPORT_ID, MAP_VIEWPORT_VERSION } from "../presentation/contracts.js";

export function validateRenderPlanWithinViewport(renderPlan, viewport, tolerance = 1e-6) {
  if (renderPlan?.renderPlanId !== MAP_RENDER_PLAN_ID || renderPlan?.renderPlanVersion !== MAP_RENDER_PLAN_VERSION) {
    throw new Error("render plan uses an incompatible contract");
  }
  if (viewport?.viewportId !== MAP_VIEWPORT_ID || viewport?.viewportVersion !== MAP_VIEWPORT_VERSION) {
    throw new Error("viewport uses an incompatible contract");
  }
  let pointCount = 0;
  for (const polygon of renderPlan.polygons || []) {
    for (const ring of polygon.rings || []) {
      for (const point of ring.points || []) {
        if (!Number.isFinite(point.x) || !Number.isFinite(point.y)) throw new TypeError("viewport point must be finite");
        if (
          point.x < viewport.padding - tolerance ||
          point.x > viewport.cssWidth - viewport.padding + tolerance ||
          point.y < viewport.padding - tolerance ||
          point.y > viewport.cssHeight - viewport.padding + tolerance
        ) {
          throw new RangeError("render-plan point falls outside the drawable viewport");
        }
        pointCount += 1;
      }
    }
  }
  if (pointCount === 0) throw new Error("render plan contains no boundary points");
  return Object.freeze({ pointCount, viewportId: viewport.viewportId, viewportVersion: viewport.viewportVersion });
}
