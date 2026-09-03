import test from "node:test";
import assert from "node:assert/strict";
import {
  SemanticZoomBand,
  resolveSemanticZoomBand,
  semanticLayerVisibility,
  resolveUnifiedLabelStyle,
} from "../../../src/map/cartography/semantic-zoom-v2.js";

test("semantic zoom uses named bands with hysteresis", () => {
  assert.equal(resolveSemanticZoomBand(1), SemanticZoomBand.NATIONAL);
  assert.equal(resolveSemanticZoomBand(1.6), SemanticZoomBand.REGIONAL);
  assert.equal(resolveSemanticZoomBand(1.5, SemanticZoomBand.REGIONAL), SemanticZoomBand.REGIONAL);
  assert.equal(resolveSemanticZoomBand(1.4, SemanticZoomBand.REGIONAL), SemanticZoomBand.NATIONAL);
  assert.equal(resolveSemanticZoomBand(2.7, SemanticZoomBand.REGIONAL), SemanticZoomBand.SUBREGIONAL);
  assert.equal(resolveSemanticZoomBand(4.3, SemanticZoomBand.SUBREGIONAL), SemanticZoomBand.LOCAL);
  assert.equal(resolveSemanticZoomBand(4.1, SemanticZoomBand.LOCAL), SemanticZoomBand.LOCAL);
  assert.equal(resolveSemanticZoomBand(3.95, SemanticZoomBand.LOCAL), SemanticZoomBand.SUBREGIONAL);
});

test("country yields before local labels and typography is screen-relative", () => {
  assert.equal(semanticLayerVisibility("COUNTRY", 1.4).label, true);
  assert.equal(semanticLayerVisibility("COUNTRY", 3).label, false);
  assert.equal(semanticLayerVisibility("CITY", 1.5).label, false);
  assert.equal(semanticLayerVisibility("CITY", 2).label, true);
  assert.equal(semanticLayerVisibility("CITY_DISTRICT", 2.5).label, false);
  assert.equal(semanticLayerVisibility("CITY_DISTRICT", 3.2).label, true);
  const country = resolveUnifiedLabelStyle("COUNTRY");
  assert.equal(country.fontSizePx, 19);
  assert.equal(country.letterSpacingPx, 0);
});
