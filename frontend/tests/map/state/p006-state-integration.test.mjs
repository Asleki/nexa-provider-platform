import test from "node:test";
import assert from "node:assert/strict";
import { createMapViewState } from "../../../src/map/state/view-state-contracts.js";
import { createMapViewStateRepository } from "../../../src/map/state/view-state-storage.js";
import { createWorldStateEnvelope } from "../../../src/map/state/world-state-contracts.js";
import { createWorldStateStore } from "../../../src/map/state/world-state-store.js";

function storageFixture() {
  const values = new Map();
  return { getItem(k) { return values.get(k) ?? null; }, setItem(k, v) { values.set(k, String(v)); }, removeItem(k) { values.delete(k); } };
}

test("P006.6 persistent view state and dynamic world state remain separate identities and versions", () => {
  const storage = storageFixture();
  const viewRepo = createMapViewStateRepository({ storage, runtimeMode: "simulation" });
  viewRepo.save(createMapViewState({ revision: 4, runtimeMode: "simulation", navigation: { zoom: 3, offsetX: 40, offsetY: -10 } }));
  const view = viewRepo.load().state;

  const worldStore = createWorldStateStore({ runtimeMode: "simulation" });
  const receipt = worldStore.apply(createWorldStateEnvelope({ revision: 1, runtimeMode: "simulation", sourceReference: "source:nexilabs:qualification", stateReferences: [] }));
  assert.equal(receipt.status, "APPLIED");
  assert.equal(view.viewStateVersion, 1);
  assert.equal(view.revision, 4);
  assert.equal(worldStore.state.worldStateVersion, 1);
  assert.equal(worldStore.state.revision, 1);
  assert.notEqual(view.viewStateId, worldStore.state.worldStateId);
  assert.equal("worldStateVersion" in view, false);
  assert.equal("viewStateVersion" in worldStore.state, false);
});
