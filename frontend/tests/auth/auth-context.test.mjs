import test from "node:test";
import assert from "node:assert/strict";
import { createAuthenticationContext, AUTH_SESSION_STORAGE_KEY } from "../../src/app/auth/auth-context.js";
import { createAuthorizationContext } from "../../src/app/auth/authorization-context.js";

function storage() {
  const values = new Map();
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => values.set(key, value),
    removeItem: (key) => values.delete(key),
  };
}

test("P006.UI.9 session identity and authorization remain separate", () => {
  const store = storage();
  const context = createAuthenticationContext({ storage: store });
  context.accept({
    sessionId: "session:1",
    principalId: "developer:1",
    identityType: "nexadevs_developer",
    runtime: "production",
    permissions: ["citizen:view"],
  });
  const authorization = createAuthorizationContext(context);
  assert.equal(context.authenticated, true);
  assert.equal(authorization.can("citizen:view"), true);
  assert.equal(authorization.can("event:approve"), false);
  const stored = JSON.parse(store.getItem(AUTH_SESSION_STORAGE_KEY));
  assert.deepEqual(stored, { sessionId: "session:1" });
  assert.equal("permissions" in stored, false);
  context.clear();
  assert.equal(context.authenticated, false);
});
