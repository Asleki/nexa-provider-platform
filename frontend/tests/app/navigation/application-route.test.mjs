import test from "node:test";
import assert from "node:assert/strict";
import { ApplicationRoute, routeFromHash, routeToHash } from "../../../src/app/navigation/application-route.js";

test("P006.UI.1 routes remain application-level and hash-addressable", () => {
  assert.equal(routeToHash(ApplicationRoute.RUNTIME_GATEWAY), "#/runtime");
  assert.equal(routeToHash(ApplicationRoute.PRODUCTION_ACCESS), "#/production");
  assert.equal(routeFromHash("#/simulation"), ApplicationRoute.SIMULATION_ENTRY);
  assert.equal(routeFromHash("#/unknown"), ApplicationRoute.RUNTIME_GATEWAY);
});
