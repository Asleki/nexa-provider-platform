import test from "node:test";
import assert from "node:assert/strict";
import { formatLatitude, formatLongitude } from "../../../src/map/presentation/coordinate-labels.js";

test("coordinate labels distinguish hemispheres and preserve zero", () => {
  assert.equal(formatLongitude(30), "30°E");
  assert.equal(formatLongitude(-30), "30°W");
  assert.equal(formatLatitude(5), "5°N");
  assert.equal(formatLatitude(-5), "5°S");
  assert.equal(formatLatitude(0), "0°");
});
