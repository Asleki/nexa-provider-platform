import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const files = [
  "src/app/account/account-enrollment-route.js",
  "src/app/account/account-enrollment-experience.js",
  "src/ui/pages/account-enrollment-gateway.js",
  "src/ui/pages/guest-account-enrollment.js",
  "src/ui/pages/developer-account-enrollment.js",
  "styles/account-enrollment-v1.css",
];
const source = files.map((path) => readFileSync(resolve(ROOT, path), "utf8")).join("\n");

test("P006.UI.10.1 frontend enrollment ships no private fixture or generated credential truth", () => {
  for (const forbidden of [
    /development\/auth\/private/i,
    /guests\.local\.json/i,
    /developers\.local\.json/i,
    /enigma_words_[345]\.csv/i,
    /guest_demo/i,
    /developer_demo/i,
    /Guest-Demo-12D!/i,
    /Developer-Demo-12D!/i,
    /credentialVerifier/i,
  ]) {
    assert.doesNotMatch(source, forbidden);
  }
});

test("P006.UI.10.1 enrollment source contains no network or browser persistence implementation", () => {
  assert.doesNotMatch(source, /\bfetch\s*\(/);
  assert.doesNotMatch(source, /localStorage|sessionStorage|indexedDB/i);
  assert.doesNotMatch(source, /navigator\.clipboard/);
});
