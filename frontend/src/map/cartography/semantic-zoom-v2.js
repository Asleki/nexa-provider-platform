/**
 * P006.7.11.15.10 — NoveGeo semantic-zoom and screen-relative typography policy.
 *
 * Presentation-only. Canonical identities, publication eligibility and API contracts
 * are deliberately outside this module.
 */

export const NOVEGEO_SEMANTIC_ZOOM_POLICY_ID = "semantic-zoom:novegeo:map-first";
export const NOVEGEO_SEMANTIC_ZOOM_POLICY_VERSION = 1;

export const SemanticZoomBand = Object.freeze({
  NATIONAL: "NATIONAL",
  REGIONAL: "REGIONAL",
  SUBREGIONAL: "SUBREGIONAL",
  LOCAL: "LOCAL",
});

const BAND_ORDER = Object.freeze([
  SemanticZoomBand.NATIONAL,
  SemanticZoomBand.REGIONAL,
  SemanticZoomBand.SUBREGIONAL,
  SemanticZoomBand.LOCAL,
]);

/**
 * enter: zoom at which the next-detailed band may be entered.
 * exit:  lower threshold used when leaving that band, providing hysteresis.
 */
export const SEMANTIC_BAND_THRESHOLDS = Object.freeze({
  [SemanticZoomBand.NATIONAL]: Object.freeze({ enter: 1, exit: 1 }),
  [SemanticZoomBand.REGIONAL]: Object.freeze({ enter: 1.55, exit: 1.42 }),
  [SemanticZoomBand.SUBREGIONAL]: Object.freeze({ enter: 2.6, exit: 2.42 }),
  [SemanticZoomBand.LOCAL]: Object.freeze({ enter: 4.25, exit: 4.0 }),
});

function positiveZoom(value) {
  const zoom = Number(value);
  if (!Number.isFinite(zoom) || zoom <= 0) throw new RangeError("zoom must be a positive finite number");
  return zoom;
}

function basicBand(zoom) {
  const z = positiveZoom(zoom);
  if (z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.LOCAL].enter) return SemanticZoomBand.LOCAL;
  if (z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.SUBREGIONAL].enter) return SemanticZoomBand.SUBREGIONAL;
  if (z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.REGIONAL].enter) return SemanticZoomBand.REGIONAL;
  return SemanticZoomBand.NATIONAL;
}

export function resolveSemanticZoomBand(zoom, previousBand = null) {
  const z = positiveZoom(zoom);
  if (!previousBand || !BAND_ORDER.includes(previousBand)) return basicBand(z);

  switch (previousBand) {
    case SemanticZoomBand.NATIONAL:
      return z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.REGIONAL].enter
        ? SemanticZoomBand.REGIONAL
        : SemanticZoomBand.NATIONAL;
    case SemanticZoomBand.REGIONAL:
      if (z < SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.REGIONAL].exit) return SemanticZoomBand.NATIONAL;
      if (z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.SUBREGIONAL].enter) return SemanticZoomBand.SUBREGIONAL;
      return SemanticZoomBand.REGIONAL;
    case SemanticZoomBand.SUBREGIONAL:
      if (z < SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.SUBREGIONAL].exit) return SemanticZoomBand.REGIONAL;
      if (z >= SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.LOCAL].enter) return SemanticZoomBand.LOCAL;
      return SemanticZoomBand.SUBREGIONAL;
    case SemanticZoomBand.LOCAL:
      return z < SEMANTIC_BAND_THRESHOLDS[SemanticZoomBand.LOCAL].exit
        ? SemanticZoomBand.SUBREGIONAL
        : SemanticZoomBand.LOCAL;
    default:
      return basicBand(z);
  }
}

export const UnifiedLayerKey = Object.freeze({
  COUNTRY: "COUNTRY",
  REGION: "REGION",
  CITY: "CITY",
  MUNICIPALITY: "MUNICIPALITY",
  CITY_DISTRICT: "CITY_DISTRICT",
  TOWN: "TOWN",
  REFERENCE: "REFERENCE",
});

const LAYER_VISIBILITY = Object.freeze({
  [UnifiedLayerKey.COUNTRY]: Object.freeze({ geometryMin: 1, geometryMax: 8, labelMin: 1, labelMax: 2.45, symbolMin: Infinity, symbolMax: -Infinity }),
  [UnifiedLayerKey.REGION]: Object.freeze({ geometryMin: 1.15, geometryMax: 8, labelMin: 1.3, labelMax: 4.1, symbolMin: Infinity, symbolMax: -Infinity }),
  [UnifiedLayerKey.CITY]: Object.freeze({ geometryMin: 1.75, geometryMax: 8, labelMin: 1.85, labelMax: 8, symbolMin: 1.85, symbolMax: 8 }),
  [UnifiedLayerKey.MUNICIPALITY]: Object.freeze({ geometryMin: 1.9, geometryMax: 8, labelMin: 2.0, labelMax: 8, symbolMin: Infinity, symbolMax: -Infinity }),
  [UnifiedLayerKey.CITY_DISTRICT]: Object.freeze({ geometryMin: 3.0, geometryMax: 8, labelMin: 3.15, labelMax: 8, symbolMin: Infinity, symbolMax: -Infinity }),
  [UnifiedLayerKey.TOWN]: Object.freeze({ geometryMin: Infinity, geometryMax: -Infinity, labelMin: 3.15, labelMax: 8, symbolMin: 3.15, symbolMax: 8 }),
  [UnifiedLayerKey.REFERENCE]: Object.freeze({ geometryMin: 1, geometryMax: 8, labelMin: 1, labelMax: 8, symbolMin: Infinity, symbolMax: -Infinity }),
});

function inside(zoom, minimum, maximum) {
  const z = positiveZoom(zoom);
  return z >= minimum && z <= maximum;
}

export function semanticLayerVisibility(layerKey, zoom) {
  const rule = LAYER_VISIBILITY[layerKey];
  if (!rule) throw new Error(`semantic visibility is not defined for layer ${layerKey}`);
  return Object.freeze({
    geometry: inside(zoom, rule.geometryMin, rule.geometryMax),
    label: inside(zoom, rule.labelMin, rule.labelMax),
    symbol: inside(zoom, rule.symbolMin, rule.symbolMax),
  });
}

export function layerKeyForLabelClass(labelClass) {
  const key = String(labelClass || "").toUpperCase();
  if (key === "COUNTRY") return UnifiedLayerKey.COUNTRY;
  if (key === "ADMIN_REGION") return UnifiedLayerKey.REGION;
  if (key === "ADMIN_CITY" || key === "CITY") return UnifiedLayerKey.CITY;
  if (key === "ADMIN_MUNICIPAL") return UnifiedLayerKey.MUNICIPALITY;
  if (key === "ADMIN_DISTRICT") return UnifiedLayerKey.CITY_DISTRICT;
  if (key === "TOWN") return UnifiedLayerKey.TOWN;
  if (key === "REFERENCE") return UnifiedLayerKey.REFERENCE;
  return null;
}

function labelStyle(values) {
  return Object.freeze({
    fontFamily: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontWeight: 600,
    fontSizePx: 12,
    letterSpacingPx: 0,
    fillStyle: "rgba(248,250,252,0.96)",
    haloStyle: "rgba(7,17,31,0.82)",
    haloWidthPx: 1.5,
    collisionPaddingPx: 3,
    labelOffsetXPx: 0,
    labelOffsetYPx: 0,
    priority: 100,
    ...values,
  });
}

/** Screen-relative sizes; geographic zoom does not continuously inflate text. */
export const UNIFIED_LABEL_STYLES = Object.freeze({
  COUNTRY: labelStyle({ priority: 1000, fontSizePx: 19, fontWeight: 650, collisionPaddingPx: 8 }),
  ADMIN_REGION: labelStyle({ priority: 900, fontSizePx: 14, fontWeight: 600, collisionPaddingPx: 5 }),
  ADMIN_CITY: labelStyle({ priority: 820, fontSizePx: 13.5, fontWeight: 650, labelOffsetYPx: -10, collisionPaddingPx: 4 }),
  CITY: labelStyle({ priority: 820, fontSizePx: 13.5, fontWeight: 650, labelOffsetYPx: -10, collisionPaddingPx: 4 }),
  ADMIN_MUNICIPAL: labelStyle({ priority: 760, fontSizePx: 12, fontWeight: 560, collisionPaddingPx: 4 }),
  ADMIN_DISTRICT: labelStyle({ priority: 650, fontSizePx: 11, fontWeight: 520, collisionPaddingPx: 3 }),
  TOWN: labelStyle({ priority: 620, fontSizePx: 11, fontWeight: 520, labelOffsetYPx: -8, collisionPaddingPx: 3 }),
  REFERENCE: labelStyle({ priority: 180, fontSizePx: 10.5, fontWeight: 500, fillStyle: "rgba(147,197,253,0.88)", haloWidthPx: 1, collisionPaddingPx: 2 }),
  NATIONAL_CAPITAL: labelStyle({ priority: 920, fontSizePx: 15.5, fontWeight: 700, labelOffsetYPx: -12, collisionPaddingPx: 5 }),
});

export function resolveUnifiedLabelStyle(labelClass, { presentationRole = null } = {}) {
  if (presentationRole === "NATIONAL_CAPITAL") return UNIFIED_LABEL_STYLES.NATIONAL_CAPITAL;
  const key = String(labelClass || "").toUpperCase();
  const style = UNIFIED_LABEL_STYLES[key];
  if (!style) throw new Error(`unified label style is not defined for ${key || "unknown"}`);
  return style;
}

export const SETTLEMENT_SYMBOL_STYLES = Object.freeze({
  CITY: Object.freeze({ radiusPx: 3.2, fillStyle: "rgba(248,250,252,0.98)", strokeStyle: "rgba(7,17,31,0.92)", strokeWidthPx: 1.4, clearancePx: 4, priority: 850 }),
  TOWN: Object.freeze({ radiusPx: 2.2, fillStyle: "rgba(248,250,252,0.94)", strokeStyle: "rgba(7,17,31,0.88)", strokeWidthPx: 1.1, clearancePx: 3, priority: 640 }),
  NATIONAL_CAPITAL: Object.freeze({ radiusPx: 4.3, fillStyle: "rgba(255,255,255,1)", strokeStyle: "rgba(7,17,31,0.96)", strokeWidthPx: 1.6, clearancePx: 5, priority: 950 }),
});

export function settlementSymbolStyle(layerKey, { presentationRole = null } = {}) {
  if (presentationRole === "NATIONAL_CAPITAL") return SETTLEMENT_SYMBOL_STYLES.NATIONAL_CAPITAL;
  if (layerKey === UnifiedLayerKey.CITY) return SETTLEMENT_SYMBOL_STYLES.CITY;
  if (layerKey === UnifiedLayerKey.TOWN) return SETTLEMENT_SYMBOL_STYLES.TOWN;
  return null;
}
