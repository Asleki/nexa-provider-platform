import test from "node:test";
import assert from "node:assert/strict";
import { createMapViewState, validateMapViewState, MAP_VIEW_STATE_ID } from "../../../src/map/state/view-state-contracts.js";

test("P006.4 view state keeps navigation, layers and selection distinct from registry authority", () => {
  const state = createMapViewState({
    revision: 3,
    runtimeMode: "simulation",
    navigation: { zoom: 2, offsetX: 25, offsetY: -10 },
    layerVisibility: { biosphere: false },
    selection: { selectedCoordinate: { longitude: 35, latitude: 1 }, source: "coordinate_search" },
  });
  assert.equal(state.viewStateId, MAP_VIEW_STATE_ID);
  assert.equal(state.revision, 3);
  assert.equal(state.navigation.zoom, 2);
  assert.equal(state.layerVisibility.biosphere, false);
  assert.deepEqual(state.selection, { longitude: 35, latitude: 1, source: "coordinate_search" });
  assert.equal("locationId" in state, false);
  assert.throws(() => validateMapViewState({ ...state, runtimeMode: "production" }, { runtimeMode: "simulation" }), /different runtime mode/);
});
