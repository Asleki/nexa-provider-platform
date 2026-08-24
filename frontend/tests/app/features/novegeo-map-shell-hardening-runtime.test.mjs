import test from "node:test";
import assert from "node:assert/strict";
import { mountNoveGeoMapShellHardeningRuntime } from "../../../src/app/features/novegeo-map-shell-hardening-runtime.js";

test("Bundle 22A mounts immediately and reconciles again after live authority completion", async () => {
  const calls = [];
  let resolveAuthority;
  const authorityRuntime = { status: "LOADING", ready: new Promise((resolve) => { resolveAuthority = resolve; }) };
  const receipt = mountNoveGeoMapShellHardeningRuntime({
    documentRef: {},
    windowRef: {},
    authorityRuntime,
    mountShellRef: () => ({
      status: "READY",
      reconcile() { calls.push("reconcile"); return { status: "READY" }; },
      disconnect() { calls.push("disconnect"); },
    }),
  });
  assert.equal(receipt.status, "READY");
  resolveAuthority({ status: "READY" });
  const ready = await receipt.ready;
  assert.equal(ready.status, "READY");
  assert.equal(ready.authorityStatus, "READY");
  assert.deepEqual(calls, ["reconcile"]);
  receipt.disconnect();
  assert.deepEqual(calls, ["reconcile", "disconnect"]);
});

test("Bundle 22A does not reconcile a route that was disconnected before authority completed", async () => {
  let resolveAuthority;
  let reconciled = false;
  const receipt = mountNoveGeoMapShellHardeningRuntime({
    authorityRuntime: { status: "LOADING", ready: new Promise((resolve) => { resolveAuthority = resolve; }) },
    mountShellRef: () => ({ status: "READY", reconcile() { reconciled = true; return { status: "READY" }; }, disconnect() {} }),
  });
  receipt.disconnect();
  resolveAuthority({ status: "READY" });
  assert.equal((await receipt.ready).status, "DISCONNECTED");
  assert.equal(reconciled, false);
});
