import test from "node:test";
import assert from "node:assert/strict";
import { mountMapPresentation } from "../../../src/map/presentation/map-presentation.js";

function fakeContext() {
  return new Proxy({ setTransform() {}, clearRect() {}, fillRect() {}, save() {}, restore() {}, beginPath() {}, moveTo() {}, lineTo() {}, stroke() {}, closePath() {}, fill() {}, setLineDash() {}, fillText() {} }, { set(target, key, value) { target[key] = value; return true; } });
}

test("map presentation mounts a canvas and returns a deterministic render receipt", () => {
  const status = { textContent: "" };
  const container = {
    dataset: {}, clientWidth: 500, clientHeight: 340,
    querySelector(selector) { return selector === "[data-role='map-render-status']" ? status : null; },
    replaceChildren(child) { this.child = child; },
    getBoundingClientRect() { return { width: 500, height: 340 }; },
  };
  const documentRef = {
    querySelector(selector) { return selector === "[data-role='future-map-viewport']" ? container : null; },
    createElement() { return { style: {}, setAttribute() {}, getContext: () => fakeContext() }; },
  };
  const receipt = mountMapPresentation(documentRef, { observeResize: false, devicePixelRatio: 1 });
  assert.equal(receipt.status, "RENDERED");
  assert.equal(container.dataset.mapStatus, "READY");
  assert.equal(status.textContent, "Map rendered");
});

test("missing map viewport degrades only the feature boundary", () => {
  const receipt = mountMapPresentation({ querySelector: () => null }, { observeResize: false });
  assert.deepEqual(receipt, { status: "UNAVAILABLE", reason: "viewport_missing" });
});
