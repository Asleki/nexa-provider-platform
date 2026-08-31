import test from "node:test";
import assert from "node:assert/strict";
import { MUNICIPALITY_MIN_ZOOM } from "../../../src/map/cartography/municipality-cartographic-overlay.js";

test("MUNICIPALITY rendering is regional-zoom gated", () => {
  assert.equal(MUNICIPALITY_MIN_ZOOM, 1.7);
});
