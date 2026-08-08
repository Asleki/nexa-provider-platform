import test from "node:test";
import assert from "node:assert/strict";
import { createNavigationState, constrainOffsets, MIN_ZOOM, MAX_ZOOM } from "../../../src/map/interaction/navigation-state.js";

test("P006.1 navigation state is immutable, versioned and bounded", () => {
  const state = createNavigationState({ zoom: 2.5, offsetX: 12, offsetY: -7, source: "test" });
  assert.equal(state.stateId, "state:novegeo:map-navigation");
  assert.equal(state.viewportStateVersion, 1);
  assert.equal(state.runtimeMode, "shared_reference");
  assert.equal(state.zoom, 2.5);
  assert.ok(Object.isFrozen(state));
  assert.equal(createNavigationState({ zoom: 0 }).zoom, MIN_ZOOM);
  assert.equal(createNavigationState({ zoom: 99 }).zoom, MAX_ZOOM);
});

test("P006.1 pan limits preserve map coverage at every zoom", () => {
  assert.deepEqual(constrainOffsets({ zoom: 1, offsetX: 999, offsetY: -999 }, { width: 400, height: 300 }), { offsetX: 0, offsetY: 0 });
  assert.deepEqual(constrainOffsets({ zoom: 2, offsetX: 999, offsetY: -999 }, { width: 400, height: 300 }), { offsetX: 200, offsetY: -150 });
});
