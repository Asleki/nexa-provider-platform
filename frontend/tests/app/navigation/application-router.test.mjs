import test from "node:test";
import assert from "node:assert/strict";
import { createApplicationRouter } from "../../../src/app/navigation/application-router.js";
import { ApplicationRoute } from "../../../src/app/navigation/application-route.js";

function fakeWindow(hash = "") {
  const listeners = new Map();
  return {
    location: { hash },
    history: { length: 1, back() {} },
    addEventListener(type, fn) { listeners.set(type, fn); },
    removeEventListener(type) { listeners.delete(type); },
  };
}

test("P006.UI.15 router moves between NexiLabs pages without touching map navigation", () => {
  const windowRef = fakeWindow();
  const seen = [];
  const router = createApplicationRouter({ windowRef, onRoute: (route) => seen.push(route) });
  router.start();
  assert.equal(router.route, ApplicationRoute.RUNTIME_GATEWAY);
  router.navigate(ApplicationRoute.PRODUCTION_ACCESS);
  assert.equal(windowRef.location.hash, "#/production");
  assert.equal(router.route, ApplicationRoute.PRODUCTION_ACCESS);
  assert.equal(seen.at(-1), ApplicationRoute.PRODUCTION_ACCESS);
});
