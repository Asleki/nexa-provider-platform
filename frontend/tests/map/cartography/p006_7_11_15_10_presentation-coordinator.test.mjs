import test from "node:test";
import assert from "node:assert/strict";
import { createNoveGeoPresentationCoordinator, PresentationMode } from "../../../src/map/cartography/presentation-coordinator.js";

class FakeNode {
  constructor(tag = "div") {
    this.tagName = tag.toUpperCase();
    this.dataset = {};
    this.style = {};
    this.children = [];
    this.hidden = false;
    this.clientWidth = 640;
    this.clientHeight = 435;
    this.attributes = {};
  }
  setAttribute(name, value) {
    this.attributes[name] = String(value);
    if (name === "data-role") this.dataset.role = String(value);
  }
  append(...nodes) { for (const node of nodes) this.appendChild(node); }
  appendChild(node) { this.children.push(node); node.parentNode = this; return node; }
  querySelector(selector) {
    if (selector === "[data-role='novegeo-map-canvas']") return this.children.find((n) => n.dataset.role === "novegeo-map-canvas") || null;
    const match = selector.match(/^\[data-role='([^']+)'\]$/);
    if (match) return this.children.find((n) => n.dataset.role === match[1]) || null;
    return null;
  }
  querySelectorAll(selector) {
    if (selector === "canvas[data-role]") return this.children.filter((n) => n.tagName === "CANVAS" && n.dataset.role);
    return [];
  }
  getBoundingClientRect() { return { width: this.clientWidth, height: this.clientHeight }; }
}

function fixture(renderFrameRef) {
  const root = new FakeNode("div");
  const page = new FakeNode("section");
  const viewport = new FakeNode("div");
  const base = new FakeNode("canvas");
  base.setAttribute("data-role", "novegeo-map-canvas");
  base.style.transform = "translate(0px, 0px) scale(1)";
  viewport.appendChild(base);
  page.querySelector = (selector) => selector === "[data-role='future-map-viewport']" ? viewport : null;
  const head = new FakeNode("head");
  const documentRef = {
    head,
    createElement: (tag) => new FakeNode(tag),
    querySelector(selector) {
      if (selector === ".novegeo-feature-page") return page;
      if (selector === "[data-role='future-map-viewport']") return viewport;
      if (selector === "#nexilabs-app") return root;
      if (selector === "link[data-novegeo-map-first-style='true']") return null;
      return null;
    },
    addEventListener() {},
    removeEventListener() {},
  };
  const windowRef = { devicePixelRatio: 1, addEventListener() {}, removeEventListener() {} };
  const coordinator = createNoveGeoPresentationCoordinator({ documentRef, windowRef, renderFrameRef });
  coordinator.attachViewport({ documentRef, windowRef });
  return { coordinator, base, viewport, page };
}

const boundary = {
  boundaryId: "boundary:novegeo:test",
  boundaryVersion: 1,
  publicationId: "publication:novegeo:test",
  coordinateReference: { coordinateReferenceId: "crs:novegeo:geographic", version: 1, axisOrder: ["longitude", "latitude"] },
  extent: { minLongitude: 30, minLatitude: -10, maxLongitude: 50, maxLatitude: 10 },
  geometry: { type: "MultiPolygon", coordinates: [[[[30,-10],[50,-10],[50,10],[30,10],[30,-10]]]] },
};
const keys = ["REGION", "CITY", "MUNICIPALITY", "CITY_DISTRICT", "TOWN"];

test("coordinator keeps one active owner and switches atomically after all snapshots", () => {
  const frame = { status: "RENDERED", semanticBand: "NATIONAL", scale: { widthPx: 80, metricLabel: "100 km", imperialLabel: "62 mi" }, visibleSubjectIds: [], collisionRejectedSubjectIds: [], sourceCandidateCount: 1, publicationEligibleCount: 1, zoomEligibleCount: 1, collisionAcceptedCount: 1, collisionRejectedCount: 0 };
  const { coordinator, base, viewport } = fixture(() => frame);
  coordinator.bindBoundary(boundary);
  assert.equal(coordinator.mode, PresentationMode.LEGACY);
  for (const key of keys.slice(0, -1)) coordinator.registerLayerSnapshot({ layerKey: key, items: [], candidates: [] });
  assert.equal(coordinator.mode, PresentationMode.LEGACY);
  coordinator.registerLayerSnapshot({ layerKey: keys.at(-1), items: [], candidates: [] });
  assert.equal(coordinator.mode, PresentationMode.UNIFIED);
  assert.equal(base.style.visibility, "hidden");
  assert.equal(viewport.querySelector("[data-role='novegeo-unified-cartographic-canvas']").style.visibility, "visible");
  assert.equal(coordinator.latestReceipt.activePresentationMode, "UNIFIED");
  assert.equal(coordinator.latestReceipt.authorityBoundary.boundaryId, boundary.boundaryId);
  assert.equal(Object.keys(coordinator.latestReceipt.snapshotSources).length, 5);
  coordinator.restoreLegacy("test_restore");
  assert.equal(coordinator.mode, PresentationMode.LEGACY);
  assert.equal(base.style.visibility, "");
});

test("failed unified frame never hides the working legacy map", () => {
  const { coordinator, base } = fixture(() => { throw new Error("synthetic_render_failure"); });
  coordinator.bindBoundary(boundary);
  for (const key of keys) coordinator.registerLayerSnapshot({ layerKey: key, items: [], candidates: [] });
  assert.equal(coordinator.mode, PresentationMode.LEGACY);
  assert.notEqual(base.style.visibility, "hidden");
  assert.match(coordinator.latestReceipt.reason, /synthetic_render_failure/);
});
