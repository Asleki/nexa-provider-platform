import test from "node:test";
import assert from "node:assert/strict";
import { captureMapViewState, restoreMapViewState } from "../../../src/map/state/view-state-runtime.js";

function controlsFixture() {
  const changes = [];
  const inputs = ["physicalLand", "biosphere", "hydrologyAtmosphere", "coordinates"].map((key) => ({
    dataset: { layerKey: key }, checked: true,
    dispatchEvent(event) { changes.push([key, event.type, this.checked]); return true; },
  }));
  const form = {
    elements: { longitude: { value: "" }, latitude: { value: "" } },
    dispatchEvent(event) { changes.push(["form", event.type, this.elements.longitude.value, this.elements.latitude.value]); return true; },
  };
  return {
    controls: {
      querySelectorAll(selector) { return selector === "[data-layer-key]" ? inputs : []; },
      querySelector(selector) { return selector === "[data-role='novegeo-coordinate-search']" ? form : null; },
    }, inputs, form, changes,
  };
}

test("P006.4 recovery replays existing Bundle 12A controller and controls without rewriting locked modules", () => {
  const calls = [];
  const discovery = {
    controller: {
      state: { zoom: 1.5, offsetX: 10, offsetY: 20 },
      reset(source) { calls.push(["reset", source]); },
      zoomTo(value, source) { calls.push(["zoom", value, source]); },
      panBy(x, y, source) { calls.push(["pan", x, y, source]); },
    },
    visibility: { physicalLand: true, biosphere: false, hydrologyAtmosphere: true, coordinates: true },
    selection: { selectedCoordinate: { longitude: 36, latitude: 2 }, source: "map_selection" },
  };
  const snapshot = captureMapViewState({ discovery, runtimeMode: "development", revision: 7 });
  assert.equal(snapshot.revision, 7);
  const { controls, changes } = controlsFixture();
  restoreMapViewState({ state: snapshot, discovery, controls, windowRef: { Event } });
  assert.deepEqual(calls, [
    ["reset", "view-state-recovery"],
    ["zoom", 1.5, "view-state-recovery"],
    ["pan", 10, 20, "view-state-recovery"],
  ]);
  assert.ok(changes.some(([key, type, checked]) => key === "biosphere" && type === "change" && checked === false));
  assert.ok(changes.some(([key, type, lon, lat]) => key === "form" && type === "submit" && lon === "36" && lat === "2"));
});
