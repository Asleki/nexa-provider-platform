import test from "node:test";
import assert from "node:assert/strict";
import { mountNoveGeoLiveAuthorityRuntime } from "../../../src/app/features/novegeo-live-authority-runtime.js";

function fakeDocument() {
  const viewport = { dataset: {} };
  const statusNode = { textContent: "" };
  const visibleStatusNode = { textContent: "", dataset: {} };
  return {
    querySelector(selector) {
      if (selector === "[data-role='future-map-viewport']") return viewport;
      if (selector === "[data-role='map-render-status']") return statusNode;
      if (selector === "[data-role='novegeo-authority-state']") return visibleStatusNode;
      return null;
    },
    viewport,
    statusNode,
    visibleStatusNode,
  };
}

const boundary = { boundaryId: "boundary:novegeo:sovereign", boundaryVersion: 2 };

test("Bundle 18 does not mount the map until API boundary authority succeeds", async () => {
  const documentRef = fakeDocument();
  const calls = [];
  const receipt = mountNoveGeoLiveAuthorityRuntime({
    documentRef,
    windowRef: { location: { hostname: "127.0.0.1", protocol: "http:", origin: "http://127.0.0.1:8765" } },
    createBoundaryClientRef: ({ apiBaseUrl }) => ({ async getActive() { calls.push(["boundary", apiBaseUrl]); return boundary; } }),
    mountFeatureRef: (options) => { calls.push(["feature", options]); return { status: "READY", disconnect() {} }; },
  });
  assert.equal(receipt.status, "LOADING");
  assert.deepEqual(calls, [["boundary", "http://127.0.0.1:8000"]]);
  assert.equal(calls.some(([kind]) => kind === "feature"), false);
  const ready = await receipt.ready;
  assert.equal(ready.status, "READY");
  assert.equal(calls[0][0], "boundary");
  assert.equal(calls[0][1], "http://127.0.0.1:8000");
  assert.equal(calls[1][0], "feature");
  assert.equal(calls[1][1].boundaryPublication, boundary);
  assert.equal(documentRef.viewport.dataset.authoritySource, "api-postgresql");
  assert.equal(documentRef.viewport.dataset.authorityBoundaryVersion, "2");
});

test("Bundle 18 fails closed and never mounts static/rendering authority when live boundary read fails", async () => {
  const documentRef = fakeDocument();
  let mounted = false;
  const receipt = mountNoveGeoLiveAuthorityRuntime({
    documentRef,
    apiBaseUrl: "http://localhost:8000",
    createBoundaryClientRef: () => ({ async getActive() { throw new Error("503"); } }),
    mountFeatureRef: () => { mounted = true; return { status: "READY" }; },
  });
  const ready = await receipt.ready;
  assert.equal(ready.status, "DEGRADED");
  assert.equal(mounted, false);
  assert.equal(documentRef.viewport.dataset.authorityStatus, "DEGRADED");
  assert.match(documentRef.statusNode.textContent, /No bundled sovereign boundary has been substituted/);
  assert.match(documentRef.visibleStatusNode.textContent, /No bundled sovereign boundary has been substituted/);
  assert.equal(documentRef.visibleStatusNode.dataset.status, "DEGRADED");
});

test("Bundle 18 cancels pending authority completion safely when route unmounts", async () => {
  const documentRef = fakeDocument();
  let resolveBoundary;
  let mounted = false;
  const receipt = mountNoveGeoLiveAuthorityRuntime({
    documentRef,
    apiBaseUrl: "http://localhost:8000",
    createBoundaryClientRef: () => ({ getActive() { return new Promise((resolve) => { resolveBoundary = resolve; }); } }),
    mountFeatureRef: () => { mounted = true; return { status: "READY" }; },
  });
  receipt.disconnect();
  resolveBoundary(boundary);
  assert.equal((await receipt.ready).status, "DISCONNECTED");
  assert.equal(mounted, false);
});
