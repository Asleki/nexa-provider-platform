import test from "node:test";
import assert from "node:assert/strict";
import { guestSignInMarkup } from "../../src/ui/pages/guest-sign-in.js";
import { developerSignInMarkup } from "../../src/ui/pages/developer-sign-in.js";
import { developerEnigmaMarkup } from "../../src/ui/pages/developer-enigma.js";
import { authenticatedTransitionMarkup } from "../../src/ui/pages/authenticated-transition.js";

test("P006.UI.6 guest flow requires username and password only", () => {
  const html = guestSignInMarkup();
  assert.match(html, /data-auth-form="guest"/);
  assert.match(html, /name="username"/);
  assert.match(html, /name="password"/);
  assert.doesNotMatch(html, /Enigma response/);
});

test("P006.UI.7 developer credentials precede P006.UI.8 Enigma", () => {
  const login = developerSignInMarkup();
  const enigma = developerEnigmaMarkup({ words: ["CAR", "TAR", "BAR"], period: "Morning", wordLength: 3 });
  assert.match(login, /data-auth-form="developer"/);
  assert.match(enigma, /CAR/);
  assert.match(enigma, /TAR/);
  assert.match(enigma, /BAR/);
  assert.match(enigma, /data-auth-form="developer-enigma"/);
  assert.doesNotMatch(enigma, /profile_lookup_word|expectedSignature/);
});

test("P006.UI.9 authenticated result remains a transition, not a Bundle 12E workspace", () => {
  const html = authenticatedTransitionMarkup({
    identityType: "guest",
    runtime: "production",
    principalId: "guest:1",
    authenticationStrength: "guest_password",
  });
  assert.match(html, /workspace integration follows in Bundle 12E/i);
  assert.doesNotMatch(html, /Citizen Registry|Approvals|Simulation Controls/);
});
