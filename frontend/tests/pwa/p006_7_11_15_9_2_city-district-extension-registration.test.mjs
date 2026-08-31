import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

test("public manifest registers CITY_DISTRICT after MUNICIPALITY", () => {
  const manifest = JSON.parse(
    fs.readFileSync("frontend/public/geography/novegeo/map-extensions/manifest.json", "utf8")
  );
  assert.deepEqual(manifest.extensions[1], {
    extensionId: "nngla-map-extension:city-district:v1",
    order: 200,
    module: "./src/app/features/novegeo-city-district-map-experience.js",
  });
});
