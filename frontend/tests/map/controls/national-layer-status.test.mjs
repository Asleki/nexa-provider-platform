import test from "node:test";
import assert from "node:assert/strict";
import {
  NATIONAL_MAP_LAYER_CATALOG,
  NationalLayerAvailability,
  createNationalLayerStatus,
  nationalLayerStatusSummary,
} from "../../../src/map/controls/national-layer-status.js";

test("Bundle 22A reserves stable future national layer keys without asserting publication", () => {
  assert.deepEqual(NATIONAL_MAP_LAYER_CATALOG.map((item) => item.key), [
    "places",
    "roads",
    "administrativeBoundaries",
    "hydrology",
    "landforms",
  ]);
  const status = createNationalLayerStatus();
  assert.ok(status.every((item) => item.availability === NationalLayerAvailability.PUBLICATION_PENDING));
  assert.ok(status.every((item) => item.enabled === false));
  assert.ok(status.every((item) => item.authoritative === false));
  assert.deepEqual(nationalLayerStatusSummary(status), { total: 5, available: 0, pending: 5 });
});

test("Bundle 22A keeps availability separate from authority and enabled presentation state", () => {
  const status = createNationalLayerStatus({
    roads: { availability: NationalLayerAvailability.AVAILABLE, enabled: true, authoritative: false },
    places: { availability: NationalLayerAvailability.AVAILABLE, enabled: true, authoritative: true },
  });
  const roads = status.find((item) => item.key === "roads");
  const places = status.find((item) => item.key === "places");
  assert.equal(roads.enabled, true);
  assert.equal(roads.authoritative, false);
  assert.equal(places.enabled, true);
  assert.equal(places.authoritative, true);
});
