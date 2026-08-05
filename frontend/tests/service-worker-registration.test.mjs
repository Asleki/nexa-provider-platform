import test from "node:test";
import assert from "node:assert/strict";
import { registerServiceWorker, ServiceWorkerStatus } from "../src/pwa/service-worker-registration.js";

function statusDocument() {
  const node = { textContent: "", dataset: {} };
  return { node, querySelectorAll: () => [node] };
}

test("unsupported browsers return an explicit non-failing receipt", async () => {
  const documentRef = statusDocument();
  const receipt = await registerServiceWorker({ navigatorRef: {}, documentRef });
  assert.equal(receipt.supported, false);
  assert.equal(receipt.status, ServiceWorkerStatus.UNSUPPORTED);
  assert.equal(documentRef.node.dataset.pwaStatus, "UNSUPPORTED");
});

test("registration uses local scope, bypasses stale HTTP cache and exposes update controls", async () => {
  const calls = [];
  const waiting = { messages: [], postMessage(message) { this.messages.push(message); } };
  const registration = {
    waiting,
    addEventListener() {},
    async update() { calls.push("update"); }
  };
  const serviceWorker = {
    controller: {},
    async register(url, options) { calls.push([url, options]); return registration; },
    addEventListener() {}
  };
  const receipt = await registerServiceWorker({ navigatorRef: { serviceWorker }, documentRef: statusDocument() });
  assert.deepEqual(calls[0], ["./sw.js", { scope: "./", updateViaCache: "none" }]);
  assert.equal(receipt.status, ServiceWorkerStatus.UPDATE_READY);
  assert.equal(receipt.activateUpdate(), true);
  assert.deepEqual(waiting.messages, [{ type: "SKIP_WAITING" }]);
  assert.equal(await receipt.checkForUpdate(), true);
});

test("registration failure is contained and reported", async () => {
  const failure = new Error("offline");
  const documentRef = statusDocument();
  const receipt = await registerServiceWorker({
    navigatorRef: { serviceWorker: { register: async () => { throw failure; } } },
    documentRef
  });
  assert.equal(receipt.status, ServiceWorkerStatus.FAILED);
  assert.equal(receipt.error, failure);
  assert.equal(documentRef.node.dataset.pwaStatus, "FAILED");
});
