import test from "node:test";
import assert from "node:assert/strict";
import { createMapNavigationController } from "../../../src/map/interaction/navigation-controller.js";

function fixture() {
  const roles = ["novegeo-map-canvas", "novegeo-physical-land-canvas", "novegeo-biosphere-canvas", "novegeo-hydrology-atmosphere-canvas", "novegeo-full-viewport-coordinate-canvas"];
  const nodes = Object.fromEntries(roles.map((role) => [role, { style: {} }]));
  const viewport = { dataset: {}, clientWidth: 400, clientHeight: 300, getBoundingClientRect: () => ({ width: 400, height: 300 }), querySelector(selector) { const match = selector.match(/data-role='([^']+)'/); return match ? nodes[match[1]] : null; } };
  return { viewport, nodes };
}

test("P006.1 one controller transforms every existing map presentation layer", () => {
  const { viewport, nodes } = fixture();
  const controller = createMapNavigationController({ viewportElement: viewport });
  controller.zoomTo(2, "test");
  controller.panBy(40, -20, "test");
  for (const node of Object.values(nodes)) {
    assert.match(node.style.transform, /scale\(2\)/);
    assert.equal(node.style.transformOrigin, "50% 50%");
  }
  assert.equal(controller.state.source, "test");
  controller.reset();
  assert.equal(controller.state.zoom, 1);
  assert.equal(controller.state.offsetX, 0);
});
