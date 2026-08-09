import test from "node:test";
import assert from "node:assert/strict";
import { createDevelopmentAuthClient, defaultDevelopmentAuthBase } from "../../src/app/auth/development-auth-client.js";

test("P006.UI.4 development auth client targets local authority without exposing fixtures", async () => {
  const calls = [];
  const fetchRef = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, status: 200, json: async () => ({ ok: true, session: { sessionId: "s1" } }) };
  };
  const client = createDevelopmentAuthClient({ fetchRef, baseUrl: "http://127.0.0.1:8766" });
  await client.loginGuest({ username: "guest", password: "secret", runtime: "production" });
  assert.equal(calls[0].url, "http://127.0.0.1:8766/auth/guest/login");
  assert.doesNotMatch(calls[0].url, /credentials|enigma_words/);
  assert.equal(defaultDevelopmentAuthBase({ location: { hostname: "localhost" } }), "http://localhost:8766");
});
