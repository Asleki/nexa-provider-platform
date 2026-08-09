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
  for (const partial of ["src/ui/partials/header.html", "src/ui/partials/footer.html"]) {
    assert.doesNotThrow(() => readFileSync(resolve(FRONTEND, partial)), partial);
  }
});

test("shell, manifest, worker and browser entry are wired as one installable boundary", () => {
  const html = readFileSync(resolve(FRONTEND, "index.html"), "utf8");
  const footer = readFileSync(resolve(FRONTEND, "src/ui/partials/footer.html"), "utf8");
  const main = readFileSync(resolve(FRONTEND, "src/main.js"), "utf8");
  assert.match(html, /manifest\.webmanifest/);
  assert.match(footer, /data-role="pwa-status"/);
  assert.match(main, /registerServiceWorker/);
  assert.match(main, /mountNexiLabsShell/);
  assert.doesNotThrow(() => readFileSync(resolve(FRONTEND, "sw.js")));
});
