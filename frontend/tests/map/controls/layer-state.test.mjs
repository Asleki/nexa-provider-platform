import test from "node:test";
import assert from "node:assert/strict";
import { MAP_LAYER_CATALOG, createLayerVisibility, applyLayerVisibility } from "../../../src/map/controls/layer-state.js";

test("P006.2 layer controls are presentation-only and map to existing P005 canvases", () => {
  const nodes = Object.fromEntries(MAP_LAYER_CATALOG.flatMap((layer) => layer.roles.map((role) => [role, { style: {} }])));
  const viewport = { querySelector(selector) { const match = selector.match(/data-role='([^']+)'/); return nodes[match?.[1]] || null; } };
  const visibility = createLayerVisibility({ biosphere: false, coordinates: false });
  applyLayerVisibility(viewport, visibility);
  assert.equal(nodes["novegeo-biosphere-canvas"].style.visibility, "hidden");
  assert.equal(nodes["novegeo-full-viewport-coordinate-canvas"].style.visibility, "hidden");
  assert.equal(nodes["novegeo-physical-land-canvas"].style.visibility, "visible");
  assert.ok(MAP_LAYER_CATALOG.every((layer) => layer.legend.length > 0));
});
