import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { ApplicationRoute, routeFromHash, routeToHash } from "../../../src/app/navigation/application-route.js";
import { createApplicationRouter } from "../../../src/app/navigation/application-router.js";
import { resolveProductionWorkspace, WorkspaceKind } from "../../../src/app/workspaces/workspace-resolution.js";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const authSource = readFileSync(resolve(ROOT, "src/app/auth/authentication-experience.js"), "utf8");
const shellSource = readFileSync(resolve(ROOT, "src/app/shell/nexilabs-shell.js"), "utf8");

function fakeWindow({ hash = "", search = "?source=pwa" } = {}) {
  const listeners = new Map();
  return {
    location: { hash, search },
    history: { length: 1, back() {} },
    addEventListener(type, listener) { listeners.set(type, listener); },
    removeEventListener(type) { listeners.delete(type); },
  };
}

test("P006.UI.17 installed source query never changes application route identity", () => {
  const windowRef = fakeWindow({ search: "?source=pwa", hash: "" });
  const seen = [];
  const router = createApplicationRouter({ windowRef, onRoute: (route) => seen.push(route) });
  assert.equal(router.start(), ApplicationRoute.RUNTIME_GATEWAY);
  assert.equal(windowRef.location.hash, routeToHash(ApplicationRoute.RUNTIME_GATEWAY));
  assert.deepEqual(seen, [ApplicationRoute.RUNTIME_GATEWAY]);
});

test("P006.UI.17 Production and Simulation NoveGeo routes remain semantically distinct", () => {
  assert.equal(routeFromHash("#/simulation/novegeo"), ApplicationRoute.SIMULATION_NOVEGEO);
  assert.equal(routeFromHash("#/production/novegeo"), ApplicationRoute.PRODUCTION_NOVEGEO);
  assert.notEqual(routeToHash(ApplicationRoute.SIMULATION_NOVEGEO), routeToHash(ApplicationRoute.PRODUCTION_NOVEGEO));
});

test("P006.UI.17 role workspace resolution never conflates Guest and Developer principals", () => {
  assert.equal(resolveProductionWorkspace({ sessionId: "s-dev", runtime: "production", identityType: "nexadevs_developer" }), WorkspaceKind.PRODUCTION_DEVELOPER);
  assert.equal(resolveProductionWorkspace({ sessionId: "s-guest", runtime: "production", identityType: "guest" }), WorkspaceKind.PRODUCTION_GUEST);
  assert.equal(resolveProductionWorkspace({ sessionId: "s-sim", runtime: "simulation", identityType: "guest" }), null);
});

test("P006.UI.17 unauthenticated Production NoveGeo remains guarded while Simulation NoveGeo can mount public simulation runtime", () => {
  assert.match(shellSource, /case ApplicationRoute\.PRODUCTION_NOVEGEO: return productionFeatureGuardMarkup\(\)/);
  assert.match(shellSource, /case ApplicationRoute\.SIMULATION_NOVEGEO: return noveGeoFeatureMarkup\(\{ runtime: "simulation"/);
  assert.match(authSource, /Authentication required/);
  assert.match(authSource, /PRODUCTION_NOVEGEO/);
});
