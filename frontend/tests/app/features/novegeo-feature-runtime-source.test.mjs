import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const source = readFileSync(resolve(ROOT, "src/app/features/novegeo-feature-runtime.js"), "utf8");
const styles = readFileSync(resolve(ROOT, "styles/app.css"), "utf8");

test("P006.UI.13 integrates the locked P004-P006 map modules instead of implementing a second map engine", () => {
  for (const marker of [
    "mountMapPresentation",
    "mountPhysicalLandPresentation",
    "mountBiospherePresentation",
    "mountHydrologyAtmospherePresentation",
    "mountFullViewportCoordinatePresentation",
    "mountMapNavigationDiscovery",
    "mountP006StateIntegration",
  ]) assert.match(source, new RegExp(marker));
  assert.doesNotMatch(source, /canonical_name|citizen registry|business registry/i);
});

test("P006.UI.13 compact screens keep controls secondary to the map while large screens may persist them", () => {
  assert.match(styles, /novegeo-map-stage/);
  assert.match(styles, /novegeo-feature-page \[data-role="future-map-viewport"\][\s\S]*width:\s*100%/);
  assert.doesNotMatch(styles, /width:\s*max\(100%,\s*48rem\)/);
  assert.match(styles, /novegeo-tool-rail/);
  assert.match(styles, /data-open-panel="false"/);
  assert.match(styles, /@media \(min-width: 64rem\)/);
});
