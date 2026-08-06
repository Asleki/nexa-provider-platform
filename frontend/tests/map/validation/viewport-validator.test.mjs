import test from "node:test";
import assert from "node:assert/strict";
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../../../src/map/presentation/publication.js";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import { createBoundaryRenderPlan } from "../../../src/map/presentation/boundary-render-plan.js";
import { validateRenderPlanWithinViewport } from "../../../src/map/validation/viewport-validator.js";

test("every rendered boundary point remains within drawable viewport bounds", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, extent: BUNDLED_WORLD_BOUNDARY_PUBLICATION.extent });
  const result = validateRenderPlanWithinViewport(createBoundaryRenderPlan(BUNDLED_WORLD_BOUNDARY_PUBLICATION, viewport), viewport);
  assert.equal(result.pointCount, 8);
});
