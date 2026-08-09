import test from "node:test";
import assert from "node:assert/strict";
import { installShellPartialRecovery } from "../../../src/app/shell/shell-recovery.js";

function makeEventTarget() {
  const listeners = new Map();
  return {
    addEventListener(type, fn) { if (!listeners.has(type)) listeners.set(type, new Set()); listeners.get(type).add(fn); },
    removeEventListener(type, fn) { listeners.get(type)?.delete(fn); },
    dispatch(type) { for (const fn of listeners.get(type) ?? []) fn({ type }); },
  };
}

test("Bundle 12.0C retries missing shell partials on foreground without reloading the route", async () => {
  const header = { innerHTML: "", dataset: {} };
  const footer = { innerHTML: "", dataset: {} };
  const docEvents = makeEventTarget();
  const windowRef = makeEventTarget();
  const documentRef = {
    ...docEvents,
    visibilityState: "visible",
    querySelector(selector) { return selector.includes("header") ? header : footer; },
  };
  let calls = 0;
  const fetchRef = async () => ({ ok: true, async text() { calls += 1; return "<div>Recovered</div>"; } });
  let recovered = 0;
  const recovery = installShellPartialRecovery({ documentRef, windowRef, fetchRef, onRecovered: () => { recovered += 1; }, timeoutMs: 50 });

  windowRef.dispatch("pageshow");
  await new Promise((resolve) => setTimeout(resolve, 10));

  assert.equal(recovery.ready, true);
  assert.equal(calls, 2);
  assert.equal(recovered, 1);
  assert.equal(header.dataset.partialReady, "true");
  assert.equal(footer.dataset.partialReady, "true");
  recovery.dispose();
});

test("Bundle 12.0C coalesces recovery while a previous retry is still in flight", async () => {
  const header = { innerHTML: "", dataset: {} };
  const footer = { innerHTML: "", dataset: {} };
  const docEvents = makeEventTarget();
  const windowRef = makeEventTarget();
  const documentRef = {
    ...docEvents,
    visibilityState: "visible",
    querySelector(selector) { return selector.includes("header") ? header : footer; },
  };
  let resolveFetch;
  const pending = new Promise((resolve) => { resolveFetch = resolve; });
  let calls = 0;
  const countedFetch = () => { calls += 1; return pending; };
  const recovery2 = installShellPartialRecovery({ documentRef, windowRef, fetchRef: countedFetch, timeoutMs: 100 });
  const first = recovery2.recover();
  const second = recovery2.recover();
  assert.equal(calls, 2); // one header + one footer batch only
  resolveFetch({ ok: false, async text() { return ""; } });
  assert.equal(await first, false);
  assert.equal(await second, false);
  recovery2.dispose();
});
