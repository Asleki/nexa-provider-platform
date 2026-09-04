import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const styleUrl = new URL("../../styles/novegeo-map-first-v1.css", import.meta.url);

test("map-first CSS is gated by MAP_FIRST layout and removes primary diagnostic clutter", async () => {
  const css = await readFile(styleUrl, "utf8");
  assert.match(css, /data-novegeo-layout-mode="MAP_FIRST"/);
  assert.match(css, /height:\s*100dvh/);
  assert.match(css, /aspect-ratio:\s*auto\s*!important/);
  assert.match(css, /\.novegeo-developer-details/);
  assert.match(css, /\.novegeo-authority-summary/);
  assert.match(css, /novegeo-unified-distance-scale/);
});

test("renderer ownership remains independently expressible after map-first layout activation", async () => {
  const css = await readFile(styleUrl, "utf8");
  assert.match(css, /data-novegeo-presentation-mode="UNIFIED"/);
  assert.match(css, /novegeo-unified-cartographic-canvas/);
});
