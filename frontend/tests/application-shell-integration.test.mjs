import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
const FRONTEND = resolve(dirname(fileURLToPath(import.meta.url)), "..");

test("application shell references only files that exist in the frontend bundle", () => {
  const html = readFileSync(resolve(FRONTEND, "index.html"), "utf8");
  const refs = [...html.matchAll(/(?:href|src)="(\.\/[^"#?]+)"/g)].map((match) => match[1]);
  assert.ok(refs.length >= 6);
  for (const ref of refs) assert.doesNotThrow(() => readFileSync(resolve(FRONTEND, ref.slice(2))), ref);
});

test("shell, manifest, worker and browser entry are wired as one installable boundary", () => {
  const html = readFileSync(resolve(FRONTEND, "index.html"), "utf8");
  const main = readFileSync(resolve(FRONTEND, "src/main.js"), "utf8");
  assert.match(html, /manifest\.webmanifest/);
  assert.match(html, /data-role="pwa-status"/);
  assert.match(main, /registerServiceWorker/);
  assert.doesNotThrow(() => readFileSync(resolve(FRONTEND, "sw.js")));
});
