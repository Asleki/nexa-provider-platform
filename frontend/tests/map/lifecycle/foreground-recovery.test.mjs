import test from "node:test";
import assert from "node:assert/strict";
import { registerMapForegroundRecovery } from "../../../src/map/lifecycle/foreground-recovery.js";

function eventTarget(initial = {}) {
  const listeners = new Map();
  return {
    ...initial,
    addEventListener(type, callback) { listeners.set(type, callback); },
    removeEventListener(type, callback) { if (listeners.get(type) === callback) listeners.delete(type); },
    fire(type, event = {}) { listeners.get(type)?.(event); },
    listeners,
  };
}

function immediate(callback) { callback(); }

test("foreground visibility restores P004 and P005 exactly once per event", () => {
  const documentRef = eventTarget({ visibilityState: "hidden", hidden: true });
  const windowRef = eventTarget();
  let mapCalls = 0;
  let physicalCalls = 0;
  const recovery = registerMapForegroundRecovery({
    documentRef,
    windowRef,
    scheduler: immediate,
    redrawMap() { mapCalls += 1; return { status: "RENDERED" }; },
    redrawPhysicalLand() { physicalCalls += 1; return { status: "RENDERED" }; },
  });

  documentRef.fire("visibilitychange");
  assert.equal(mapCalls, 0);
  documentRef.visibilityState = "visible";
  documentRef.hidden = false;
  documentRef.fire("visibilitychange");
  assert.equal(mapCalls, 1);
  assert.equal(physicalCalls, 1);
  assert.equal(recovery.repaintCount, 1);
  assert.equal(recovery.latestReceipt.status, "REPAINTED");
});

test("pageshow restoration reuses the same governed repaint path", () => {
  const documentRef = eventTarget({ visibilityState: "visible", hidden: false });
  const windowRef = eventTarget();
  let mapCalls = 0;
  let physicalCalls = 0;
  const recovery = registerMapForegroundRecovery({
    documentRef,
    windowRef,
    scheduler: immediate,
    redrawMap() { mapCalls += 1; return { status: "RENDERED" }; },
    redrawPhysicalLand() { physicalCalls += 1; return { status: "RENDERED" }; },
  });

  windowRef.fire("pageshow", { persisted: true });
  assert.equal(mapCalls, 1);
  assert.equal(physicalCalls, 1);
  recovery.disconnect();
  windowRef.fire("pageshow", { persisted: true });
  assert.equal(mapCalls, 1);
});

test("coalesces duplicate foreground signals before the scheduled repaint", () => {
  const documentRef = eventTarget({ visibilityState: "visible", hidden: false });
  const windowRef = eventTarget();
  const queue = [];
  let mapCalls = 0;
  const recovery = registerMapForegroundRecovery({
    documentRef,
    windowRef,
    scheduler(callback) { queue.push(callback); },
    redrawMap() { mapCalls += 1; return { status: "RENDERED" }; },
    redrawPhysicalLand() { return { status: "RENDERED" }; },
  });

  documentRef.fire("visibilitychange");
  windowRef.fire("pageshow");
  assert.equal(queue.length, 1);
  queue.shift()();
  assert.equal(mapCalls, 1);
  assert.equal(recovery.repaintCount, 1);
});
