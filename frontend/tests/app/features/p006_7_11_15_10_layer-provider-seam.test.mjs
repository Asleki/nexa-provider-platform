import test from "node:test";
import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";

const governedFiles = [
  "novegeo-region-map-experience.js",
  "novegeo-city-map-experience.js",
  "novegeo-municipality-map-experience.js",
  "novegeo-city-district-map-experience.js",
  "novegeo-town-map-experience.js",
];

test("governed layer adapters retain legacy overlay fallback and lazily resolve the shell-installed coordinator", async () => {
  for (const file of governedFiles) {
    const source = await readFile(new URL(`../../../src/app/features/${file}`, import.meta.url), "utf8");
    assert.match(source, /presentationCoordinator\s*=\s*undefined/);
    assert.match(source, /resolveNoveGeoPresentationCoordinator\(presentationCoordinator\)/);
    assert.match(source, /registerNoveGeoPresentationSnapshot/);
    assert.match(source, /mountOverlayRef/);
    assert.match(source, /unifiedPresentationOwnsLayer/);
    const legacyMountIndex = source.indexOf("overlay = mountOverlayRef(documentRef");
    const snapshotIndex = source.indexOf("const coordination = registerNoveGeoPresentationSnapshot");
    assert.ok(legacyMountIndex >= 0, `${file} must retain the legacy overlay`);
    assert.ok(snapshotIndex > legacyMountIndex, `${file} must prepare legacy fallback before snapshot activation`);
    assert.doesNotMatch(source, /Bundle19B|DOM scraping|querySelectorAll\([^)]*subject/);
  }
});

test("country styling prepares its legacy label overlay before boundary binding can activate UNIFIED", async () => {
  const source = await readFile(
    new URL("../../../src/app/features/novegeo-cartographic-styling-experience.js", import.meta.url),
    "utf8",
  );
  assert.match(source, /resolveNoveGeoPresentationCoordinator\(presentationCoordinator\)/);
  const legacyMount = source.indexOf("overlay = mountOverlayRef(documentRef");
  const bind = source.indexOf("presentationCoordinator?.bindBoundary?.(boundary)");
  assert.ok(legacyMount >= 0);
  assert.ok(bind > legacyMount, "country legacy fallback must exist before UNIFIED activation is possible");
});
