import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { createBoundaryRenderPlan } from "../../../src/map/presentation/boundary-render-plan.js";

test("governed irregular NoveGeo boundary is preserved as a MultiPolygon render plan", () => {
  const viewport = createViewport({ cssWidth: 640, cssHeight: 420, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const plan = createBoundaryRenderPlan(BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport);
  assert.equal(plan.boundaryId, "boundary:novegeo:sovereign");
  assert.equal(plan.polygons.length, 1);
  assert.equal(plan.polygons[0].rings[0].points.length, 8);
  const uniqueX = new Set(plan.polygons[0].rings[0].points.map((point) => point.x.toFixed(4)));
  const uniqueY = new Set(plan.polygons[0].rings[0].points.map((point) => point.y.toFixed(4)));
  assert.ok(uniqueX.size > 4);
  assert.ok(uniqueY.size > 4);
});
