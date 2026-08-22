import test from "node:test";
import assert from "node:assert/strict";
import { noveGeoFeatureMarkup } from "../../../src/ui/pages/novegeo-feature.js";

test("Bundle 18 NoveGeo page exposes a visible live-authority state region", () => {
  const markup = noveGeoFeatureMarkup({ runtime: "simulation" });
  assert.match(markup, /data-role="novegeo-authority-state"/);
  assert.match(markup, /role="status"/);
  assert.match(markup, /authoritative NoveGeo read API/i);
});
