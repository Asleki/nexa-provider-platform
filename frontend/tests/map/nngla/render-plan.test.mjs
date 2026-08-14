import test from "node:test";
import assert from "node:assert/strict";
import { createNnglaRenderPlan } from "../../../src/map/nngla/render-plan.js";

test("P006.7.9 map plan never invents coordinates for non-renderable public registry records", () => {
  const plan = createNnglaRenderPlan([{ subjectId: "NGP-1", family: "PLACE", displayName: "Example", publicEligible: true, mapRenderable: false, geometryReference: null }]);
  assert.equal(plan.renderable.length, 0);
  assert.equal(plan.deferred.length, 1);
  assert.equal(plan.inventedCoordinates, false);
  assert.equal("latitude" in plan.deferred[0], false);
});

test("P006.7.9 map-renderable record requires an authoritative geometry reference", () => {
  assert.throws(() => createNnglaRenderPlan([{ subjectId: "NGP-1", family: "PLACE", displayName: "Example", publicEligible: true, mapRenderable: true, geometryReference: null }]), /geometryReference/);
});

test("P006.7.9 render plan rejects records that are not publication eligible", () => {
  assert.throws(() => createNnglaRenderPlan([{ subjectId: "NGP-1", family: "PLACE", displayName: "Example", publicEligible: false, mapRenderable: false, geometryReference: null }]), /public-eligible/);
});
