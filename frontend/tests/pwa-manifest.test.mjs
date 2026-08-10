import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const manifest = JSON.parse(readFileSync(resolve(ROOT, "public/manifest.webmanifest"), "utf8"));
const html = readFileSync(resolve(ROOT, "index.html"), "utf8");

test("manifest has governed install metadata and local start scope", () => {
  assert.equal(manifest.name, "NexiLabs PWA");
  assert.equal(manifest.short_name, "NexiLabs");
  assert.equal(manifest.id, "../");
  assert.equal(manifest.start_url, "../?source=pwa");
  assert.equal(manifest.scope, "../");
  assert.equal(manifest.display, "standalone");
  assert.equal(manifest.theme_color, "#0D1B2A");
});

test("manifest provides any and maskable canonical icons", () => {
  const purposes = new Set(manifest.icons.map((icon) => icon.purpose));
  assert.deepEqual(purposes, new Set(["any", "maskable"]));
  for (const icon of manifest.icons) {
    assert.equal(icon.src.startsWith("./brand/nexilabs/pwa/"), true);
    assert.equal(icon.type, "image/png");
  }
});

test("application document links manifest, theme and apple metadata", () => {
  assert.match(html, /rel="manifest" href="\.\/public\/manifest\.webmanifest"/);
  assert.match(html, /name="theme-color" content="#0D1B2A"/);
  assert.match(html, /rel="apple-touch-icon"/);
});


test("P006.UI.16 manifest-relative URLs resolve to the application root, not the public asset directory", () => {
  const manifestUrl = new URL("https://example.test/nexilabs/public/manifest.webmanifest");
  assert.equal(new URL(manifest.id, manifestUrl).href, "https://example.test/nexilabs/");
  assert.equal(new URL(manifest.start_url, manifestUrl).href, "https://example.test/nexilabs/?source=pwa");
  assert.equal(new URL(manifest.scope, manifestUrl).href, "https://example.test/nexilabs/");
});
