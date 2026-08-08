import test from "node:test";
import assert from "node:assert/strict";
import { createMapViewState } from "../../../src/map/state/view-state-contracts.js";
import { createMapViewStateRepository, mapViewStateStorageKey } from "../../../src/map/state/view-state-storage.js";

function storageFixture() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); },
    values,
  };
}

test("P006.4 persistence is runtime-scoped and restores only compatible view state", () => {
  const storage = storageFixture();
  const simulation = createMapViewStateRepository({ storage, runtimeMode: "simulation" });
  const production = createMapViewStateRepository({ storage, runtimeMode: "production" });
  assert.notEqual(simulation.key, production.key);
  assert.equal(simulation.key, mapViewStateStorageKey("simulation"));
  simulation.save(createMapViewState({ revision: 1, runtimeMode: "simulation" }));
  assert.equal(simulation.load().status, "RESTORED");
  assert.equal(production.load().status, "EMPTY");
});

test("P006.4 corrupted browser view state is rejected and cleared rather than trusted", () => {
  const storage = storageFixture();
  const repo = createMapViewStateRepository({ storage, runtimeMode: "development" });
  storage.setItem(repo.key, "{not-json");
  const result = repo.load();
  assert.equal(result.status, "REJECTED");
  assert.equal(storage.getItem(repo.key), null);
});
