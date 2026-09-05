import test from "node:test";
import assert from "node:assert/strict";
import {
  AccountEnrollmentRoute,
  isAccountEnrollmentRoute,
  accountEnrollmentRouteToHash,
  accountEnrollmentRouteFromHash,
} from "../../src/app/account/account-enrollment-route.js";
import { ApplicationRoute, routeFromHash } from "../../src/app/navigation/application-route.js";

const routes = Object.values(AccountEnrollmentRoute);

test("P006.UI.10.1.1 account enrollment owns a separate deterministic route namespace", () => {
  assert.equal(routes.length, 11);
  assert.equal(new Set(routes).size, routes.length);
  assert.deepEqual(routes.filter((route) => Object.values(ApplicationRoute).includes(route)), []);
  for (const route of routes) {
    assert.equal(isAccountEnrollmentRoute(route), true);
    const hash = accountEnrollmentRouteToHash(route);
    assert.match(hash, /^#\/account(?:\/|$)/);
    assert.equal(accountEnrollmentRouteFromHash(hash), route);
  }
});

test("P006.UI.10.1.1 account route parser never converts unknown hashes into enrollment routes", () => {
  assert.equal(accountEnrollmentRouteFromHash("#/runtime"), null);
  assert.equal(accountEnrollmentRouteFromHash("#/production"), null);
  assert.equal(accountEnrollmentRouteFromHash("#/simulation"), null);
  assert.equal(accountEnrollmentRouteFromHash("#/account/unknown"), null);
  assert.throws(() => accountEnrollmentRouteToHash("production"), /Unsupported account-enrollment route/);
});


test("P006.UI.10.1.1 enrollment hashes coexist additively with the locked application router", () => {
  assert.equal(routeFromHash("#/account"), ApplicationRoute.RUNTIME_GATEWAY);
  assert.equal(accountEnrollmentRouteFromHash("#/account"), AccountEnrollmentRoute.GATEWAY);
  assert.equal(routeFromHash("#/production"), ApplicationRoute.PRODUCTION_ACCESS);
  assert.equal(accountEnrollmentRouteFromHash("#/production"), null);
});
