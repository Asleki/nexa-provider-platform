import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = resolve(dirname(fileURLToPath(import.meta.url)), "../../..");
const source = readFileSync(resolve(ROOT, "src/app/features/novegeo-feature-runtime.js"), "utf8");

test("Bundle 18 low-level NoveGeo runtime injects one authority boundary into every locked renderer", () => {
  assert.match(source, /boundaryPublication = null/);
  assert.match(source, /publication: boundaryPublication/);
  assert.match(source, /mountPhysicalLandPresentation\(documentRef, \{ boundaryPublication \}\)/);
  assert.match(source, /mountBiospherePresentation\(documentRef, \{ boundaryPublication \}\)/);
  assert.match(source, /mountHydrologyAtmospherePresentation\(documentRef, \{ boundaryPublication \}\)/);
  assert.match(source, /mountFullViewportCoordinatePresentation\(documentRef, \{ boundaryPublication \}\)/);
  assert.match(source, /mountMapNavigationDiscovery\(documentRef, windowRef, \{ publication: boundaryPublication \}\)/);
});

test("Bundle 18 keeps the historical runtime callable while allowing an additive live NNGLA status mount", () => {
  assert.match(source, /nnglaPublicationMount = mountNnglaPublicationStatus/);
  assert.match(source, /nnglaPublicationMount\(\{ documentRef/);
});
