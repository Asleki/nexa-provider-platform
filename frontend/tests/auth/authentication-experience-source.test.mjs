import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");
const main = readFileSync(resolve(ROOT, "src/main.js"), "utf8");
const experience = readFileSync(resolve(ROOT, "src/app/auth/authentication-experience.js"), "utf8");
const worker = readFileSync(resolve(ROOT, "sw.js"), "utf8");

test("Bundle 12D integrates additively without rewriting the locked Bundle 12C shell", () => {
  assert.match(main, /authentication-experience\.js/);
  assert.match(experience, /PRODUCTION_DEVELOPER/);
  assert.match(experience, /PRODUCTION_GUEST/);
  assert.doesNotMatch(worker, /development\/auth\/private|guests\.local\.json|developers\.local\.json|enigma_words_/);
});

test("Bundle 12E resolves authenticated Production principals into role workspaces and guards Production NoveGeo", () => {
  assert.match(experience, /resolveProductionWorkspace/);
  assert.match(experience, /productionDeveloperWorkspaceMarkup/);
  assert.match(experience, /productionGuestWorkspaceMarkup/);
  assert.match(experience, /PRODUCTION_NOVEGEO/);
  assert.match(experience, /Authentication required/);
});
