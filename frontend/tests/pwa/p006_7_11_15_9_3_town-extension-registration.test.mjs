import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

test("public manifest registers TOWN after CITY_DISTRICT", () => {
  const manifest = JSON.parse(
    fs.readFileSync("frontend/public/geography/novegeo/map-extensions/manifest.json", "utf8")
  );
  assert.deepEqual(manifest.extensions[2], {
    extensionId: "nngla-map-extension:town:v1",
    order: 300,
    module: "./src/app/features/novegeo-town-map-experience.js",
  });
});
