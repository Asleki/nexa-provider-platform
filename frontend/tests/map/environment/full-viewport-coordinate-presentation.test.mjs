import test from "node:test";
import assert from "node:assert/strict";
import { createViewport } from "../../../src/map/presentation/viewport.js";
import {
  createFullViewportCoordinatePlan,
  mountFullViewportCoordinatePresentation,
} from "../../../src/map/environment/full-viewport-coordinate-presentation.js";

function fakeContext() {
  return new Proxy({
    setTransform() {}, clearRect() {}, save() {}, restore() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {}, setLineDash() {},
  }, { set(target, key, value) { target[key] = value; return true; } });
}

function fakeDocument() {
  const boundary = { style: {}, getContext: () => fakeContext() };
  const children = [boundary];
  const container = {
    style: {}, clientWidth: 500,
    getBoundingClientRect() { return { width: 500, height: 340 }; },
    querySelector(selector) {
      if (selector === "[data-role='novegeo-map-canvas']") return boundary;
      if (selector === "[data-role='novegeo-full-viewport-coordinate-canvas']") {
        return children.find((node) => node.role === "novegeo-full-viewport-coordinate-canvas") || null;
      }
      return null;
    },
    appendChild(node) { children.push(node); },
  };
  return {
    container,
    children,
    querySelector(selector) { return selector === "[data-role='future-map-viewport']" ? container : null; },
    createElement() {
      return {
        role: null, style: {}, width: 0, height: 0,
        setAttribute(name, value) { if (name === "data-role") this.role = value; },
        getContext: () => fakeContext(),
      };
    },
  };
}

test("full-viewport plan extends longitude, latitude and equator to map-frame edges", () => {
  const viewport = createViewport({ cssWidth: 600, cssHeight: 400, padding: 24, extent: { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 } });
  const plan = createFullViewportCoordinatePlan(viewport, { longitudeInterval: 5, latitudeInterval: 5 });
  assert.deepEqual(plan.longitudeLines.map((line) => line.value), [30, 35, 40, 45]);
  assert.ok(plan.longitudeLines.every((line) => line.start.y === 0 && line.end.y === 400));
  assert.ok(plan.latitudeLines.every((line) => line.start.x === 0 && line.end.x === 600));
  assert.equal(plan.equator.start.x, 0);
  assert.equal(plan.equator.end.x, 600);
});

test("full-viewport coordinate presentation is additive and idempotently reuses one overlay canvas", () => {
  const documentRef = fakeDocument();
  const first = mountFullViewportCoordinatePresentation(documentRef, { devicePixelRatio: 1 });
  const second = mountFullViewportCoordinatePresentation(documentRef, { devicePixelRatio: 1 });
  assert.equal(first.status, "RENDERED");
  assert.equal(first.frameCoverage, "full_viewport");
  assert.equal(second.status, "RENDERED");
  assert.equal(documentRef.children.filter((node) => node.role === "novegeo-full-viewport-coordinate-canvas").length, 1);
  const overlay = documentRef.children.find((node) => node.role === "novegeo-full-viewport-coordinate-canvas");
  assert.equal(overlay.style.zIndex, "3");
  assert.equal(overlay.style.pointerEvents, "none");
});
