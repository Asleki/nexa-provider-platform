import test from "node:test";
import assert from "node:assert/strict";
import { createApplication } from "../src/app/application.js";
import { createRuntimeConfig } from "../src/config/runtime-config.js";

function element() {
  return { dataset: {}, textContent: "" };
}

function fakeDocument({ includeRoot = true } = {}) {
  const root = includeRoot ? element() : null;
  const status = element();
  const runtime = element();
  const version = element();
  const selectors = new Map([
    ["#nexilabs-app", root],
    ["[data-role='application-status']", status],
    ["[data-role='runtime-mode']", runtime],
    ["[data-role='application-version']", version],
  ]);
  return {
    querySelector(selector) { return selectors.get(selector) ?? null; },
    nodes: { root, status, runtime, version },
  };
}

test("application mounts and returns a deterministic READY receipt", () => {
  const documentRef = fakeDocument();
  const config = createRuntimeConfig({ runtimeMode: "testing", buildReference: "test-build" });
  const app = createApplication({ documentRef, config, clock: () => "ready-time" });
  const receipt = app.start();

  assert.equal(receipt.status, "READY");
  assert.equal(receipt.runtimeMode, "testing");
  assert.equal(receipt.readyAt, "ready-time");
  assert.equal(documentRef.nodes.root.dataset.applicationStatus, "READY");
  assert.equal(documentRef.nodes.root.dataset.runtimeMode, "testing");
  assert.equal(documentRef.nodes.status.textContent, "Ready");
  assert.equal(documentRef.nodes.runtime.textContent, "testing");
});

test("start is idempotent after successful startup", () => {
  const documentRef = fakeDocument();
  const app = createApplication({ documentRef, config: createRuntimeConfig() });
  assert.equal(app.start(), app.start());
  assert.equal(app.state.sequence, 2);
});

test("missing application root moves lifecycle to FAILED", () => {
  const app = createApplication({ documentRef: fakeDocument({ includeRoot: false }), config: createRuntimeConfig() });
  assert.throws(() => app.start(), /Required application element not found/);
  assert.equal(app.state.status, "FAILED");
  assert.equal(app.state.details.reason, "bootstrap_failure");
});
