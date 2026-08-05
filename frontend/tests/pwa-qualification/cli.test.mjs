import test from "node:test";
import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../..");

test("offline qualification CLI exits cleanly and prints receipt", () => {
  const run = spawnSync(process.execPath, [resolve(ROOT, "scripts/qualify-offline-pwa.mjs")], { encoding: "utf8" });
  assert.equal(run.status, 0, run.stderr);
  assert.match(run.stdout, /Status: PASSED/);
  assert.match(run.stdout, /Database writes performed: 0/);
});
