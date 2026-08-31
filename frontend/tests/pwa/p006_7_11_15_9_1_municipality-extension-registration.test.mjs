import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";

test("frontend CM1 manifest registers MUNICIPALITY additively", () => {
  const payload = JSON.parse(
    fs.readFileSync(
      "frontend/public/geography/novegeo/map-extensions/manifest.json",
      "utf8"
    )
  );
  assert.equal(payload.manifestVersion, 1);
  assert.deepEqual(payload.extensions[0], {
    extensionId: "nngla-map-extension:municipality:v1",
    order: 100,
    module: "./src/app/features/novegeo-municipality-map-experience.js",
  });
});
