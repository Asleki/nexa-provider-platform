import test from "node:test";
import assert from "node:assert/strict";
import { normalizeUiRect, qualifyMapShellSafeArea, uiRectsIntersect } from "../../../src/map/validation/map-shell-safe-area.js";

test("Bundle 22A treats edge-adjacent toolbar space as clear rather than map overlap", () => {
  const viewport = { left: 0, top: 60, right: 360, bottom: 500 };
  const toolbar = { left: 0, top: 0, right: 360, bottom: 60 };
  assert.equal(uiRectsIntersect(viewport, toolbar), false);
  assert.deepEqual(qualifyMapShellSafeArea({ viewportRect: viewport, permanentControlRects: [{ id: "toolbar", rect: toolbar }] }), {
    status: "CLEAR",
    overlapCount: 0,
    overlaps: [],
  });
});

test("Bundle 22A detects a permanent control that covers material geography", () => {
  const result = qualifyMapShellSafeArea({
    viewportRect: { left: 0, top: 60, right: 360, bottom: 500 },
    permanentControlRects: [{ id: "legacy-right-rail", rect: { left: 312, top: 80, right: 356, bottom: 350 } }],
  });
  assert.equal(result.status, "OVERLAP");
  assert.equal(result.overlapCount, 1);
  assert.deepEqual(result.overlaps, ["legacy-right-rail"]);
});

test("Bundle 22A safe-area qualification fails neutral when layout cannot be measured", () => {
  assert.equal(normalizeUiRect({ left: "bad" }), null);
  assert.equal(qualifyMapShellSafeArea({ viewportRect: null }).status, "UNMEASURED");
});
