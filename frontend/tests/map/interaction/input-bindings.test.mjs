import test from "node:test";
import assert from "node:assert/strict";
import { bindMapNavigationInputs } from "../../../src/map/interaction/input-bindings.js";

function target() {
  const listeners = new Map();
  return { style: {}, attrs: {}, addEventListener(t, h) { listeners.set(t, h); }, removeEventListener(t) { listeners.delete(t); }, setAttribute(k, v) { this.attrs[k] = v; }, hasAttribute(k) { return k in this.attrs; }, fire(t, e = {}) { listeners.get(t)?.({ preventDefault() {}, ...e }); }, listeners };
}

test("P006.1 keyboard and wheel inputs converge on the same controller", () => {
  const viewport = target();
  const calls = [];
  const controller = { panBy(...args) { calls.push(["pan", ...args]); }, zoomBy(...args) { calls.push(["zoom", ...args]); }, reset(...args) { calls.push(["reset", ...args]); } };
  const binding = bindMapNavigationInputs({ viewportElement: viewport, controller });
  viewport.fire("keydown", { key: "ArrowRight" });
  viewport.fire("keydown", { key: "+" });
  viewport.fire("wheel", { deltaY: 10 });
  assert.equal(calls[0][0], "pan");
  assert.equal(calls[1][0], "zoom");
  assert.equal(calls[2][0], "zoom");
  assert.equal(viewport.attrs.tabindex, "0");
  assert.equal(viewport.style.touchAction, "none");
  binding.disconnect();
  assert.equal(viewport.listeners.size, 0);
});
