import test from "node:test";
import assert from "node:assert/strict";
import {
  NOVEGEO_COMPACT_OPENING_ZOOM,
  defaultNoveGeoOpeningZoom,
  applyDefaultNoveGeoOpeningView,
  createNoveGeoResizeCoordinator,
} from "../../../src/app/features/novegeo-feature-geometry.js";

function viewport(width = 360) {
  return {
    clientWidth: width,
    getBoundingClientRect() { return { width }; },
  };
}

function discovery(zoom = 1) {
  let state = { zoom, offsetX: 0, offsetY: 0, revision: 0 };
  const calls = [];
  return {
    calls,
    controller: {
      get state() { return state; },
      zoomTo(next, source) {
        calls.push({ next, source });
        state = { ...state, zoom: Number(next), revision: state.revision + 1 };
        return state;
      },
    },
  };
}

test("Bundle 12E Omega uses controller state—not oversized CSS—as the compact opening magnification", () => {
  assert.equal(defaultNoveGeoOpeningZoom({ viewportWidth: 360 }), NOVEGEO_COMPACT_OPENING_ZOOM);
  assert.equal(defaultNoveGeoOpeningZoom({ viewportWidth: 1280 }), 1);
  const d = discovery(1);
  const receipt = applyDefaultNoveGeoOpeningView({ viewport: viewport(360), discovery: d, stateIntegration: { viewState: { latestReceipt: { status: "EMPTY" } } } });
  assert.equal(receipt.status, "READY");
  assert.equal(d.controller.state.zoom, 1.25);
  assert.deepEqual(d.calls, [{ next: 1.25, source: "feature-opening-view" }]);
});

test("Bundle 12E Omega preserves restored runtime-scoped view state instead of forcing an opening zoom", () => {
  const d = discovery(2);
  const receipt = applyDefaultNoveGeoOpeningView({ viewport: viewport(360), discovery: d, stateIntegration: { viewState: { latestReceipt: { status: "RESTORED" } } } });
  assert.equal(receipt.status, "PRESERVED");
  assert.equal(d.controller.state.zoom, 2);
  assert.equal(d.calls.length, 0);
});

test("Bundle 12E Omega resize reconciliation redraws the feature surface and reconstrains the existing zoom", () => {
  let width = 360;
  const vp = { getBoundingClientRect: () => ({ width }), clientWidth: 360 };
  const d = discovery(1.25);
  let redraws = 0;
  const listeners = new Map();
  class FakeResizeObserver {
    constructor(callback) { this.callback = callback; }
    observe() {}
    disconnect() {}
  }
  const windowRef = {
    ResizeObserver: FakeResizeObserver,
    addEventListener(type, fn) { listeners.set(type, fn); },
    removeEventListener(type) { listeners.delete(type); },
  };
  const coordinator = createNoveGeoResizeCoordinator({ viewport: vp, windowRef, discovery: d, redraw: () => { redraws += 1; return { status: "REDRAWN" }; } });
  width = 1024;
  const receipt = coordinator.reconcile();
  assert.equal(receipt.status, "READY");
  assert.equal(redraws, 1);
  assert.deepEqual(d.calls.at(-1), { next: 1.25, source: "feature-viewport-resize" });
  coordinator.disconnect();
});
