import assert from "node:assert/strict";
import test from "node:test";

import { renderWorldGeometryStatus } from "../../../src/map/geography/status.js";

function element() { return { textContent: "" }; }

test("P004 status integration reports authority without claiming a renderer", () => {
  const nodes = new Map([
    ["[data-role='world-boundary-status']", element()],
    ["[data-role='coordinate-reference-status']", element()],
    ["[data-role='projection-status']", element()],
  ]);
  const receipt = renderWorldGeometryStatus({ querySelector: selector => nodes.get(selector) || null });
  assert.equal(receipt.boundaryReady, true);
  assert.match(nodes.get("[data-role='projection-status']").textContent, /equirectangular/);
});
