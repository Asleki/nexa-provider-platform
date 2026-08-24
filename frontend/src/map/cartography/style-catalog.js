/** P006.7.11.15.4 — versioned NoveGeo cartographic style and label hierarchy. */
import { CartographicLabelClass } from "./contracts.js";

export const CARTOGRAPHIC_STYLE_CATALOG_ID = "style-catalog:novegeo:cartography";
export const CARTOGRAPHIC_STYLE_CATALOG_VERSION = 1;

function style(labelClass, values) {
  return Object.freeze({
    styleKey: `NOVEGEO_${labelClass}`,
    labelClass,
    minZoom: 1,
    maxZoom: 8,
    priority: 100,
    fontFamily: "system-ui, sans-serif",
    fontWeight: 700,
    fontSizePx: 12,
    maxFontSizePx: 18,
    fontScalePerZoom: 0.05,
    letterSpacingPx: 0,
    fillStyle: "rgba(248,250,252,0.92)",
    haloStyle: "rgba(7,17,31,0.96)",
    haloWidthPx: 3,
    collisionPaddingPx: 4,
    textTransform: "none",
    ...values,
  });
}

export const CARTOGRAPHIC_STYLES = Object.freeze({
  [CartographicLabelClass.COUNTRY]: style(CartographicLabelClass.COUNTRY, {
    priority: 1000, minZoom: 1, maxZoom: 4.25, fontWeight: 800, fontSizePx: 21,
    maxFontSizePx: 30, fontScalePerZoom: 0.12, letterSpacingPx: 3,
    haloWidthPx: 4, collisionPaddingPx: 10, textTransform: "uppercase",
  }),
  [CartographicLabelClass.ADMIN_REGION]: style(CartographicLabelClass.ADMIN_REGION, { priority: 900, minZoom: 1.15, fontSizePx: 15, maxFontSizePx: 21 }),
  [CartographicLabelClass.ADMIN_DISTRICT]: style(CartographicLabelClass.ADMIN_DISTRICT, { priority: 820, minZoom: 1.45, fontSizePx: 13, maxFontSizePx: 18 }),
  [CartographicLabelClass.ADMIN_MUNICIPAL]: style(CartographicLabelClass.ADMIN_MUNICIPAL, { priority: 780, minZoom: 1.7, fontSizePx: 13, maxFontSizePx: 17 }),
  [CartographicLabelClass.ADMIN_CITY]: style(CartographicLabelClass.ADMIN_CITY, { priority: 750, minZoom: 1.85, fontSizePx: 13, maxFontSizePx: 17 }),
  [CartographicLabelClass.CITY]: style(CartographicLabelClass.CITY, { priority: 720, minZoom: 1.35, fontSizePx: 14, maxFontSizePx: 20, fontWeight: 800 }),
  [CartographicLabelClass.TOWN]: style(CartographicLabelClass.TOWN, { priority: 620, minZoom: 1.8, fontSizePx: 12, maxFontSizePx: 17 }),
  [CartographicLabelClass.VILLAGE]: style(CartographicLabelClass.VILLAGE, { priority: 520, minZoom: 2.2, fontSizePx: 11, maxFontSizePx: 15, fontWeight: 650 }),
  [CartographicLabelClass.LOCALITY]: style(CartographicLabelClass.LOCALITY, { priority: 420, minZoom: 2.8, fontSizePx: 10, maxFontSizePx: 14, fontWeight: 600 }),
  [CartographicLabelClass.ROAD_ROUTE]: style(CartographicLabelClass.ROAD_ROUTE, { priority: 360, minZoom: 2.4, fontSizePx: 10, maxFontSizePx: 13, fontWeight: 800 }),
  [CartographicLabelClass.ROAD_NAME]: style(CartographicLabelClass.ROAD_NAME, { priority: 330, minZoom: 3, fontSizePx: 10, maxFontSizePx: 13, fontWeight: 600 }),
  [CartographicLabelClass.HYDROLOGY]: style(CartographicLabelClass.HYDROLOGY, { priority: 340, minZoom: 1.55, fontSizePx: 11, maxFontSizePx: 15, fontWeight: 650 }),
  [CartographicLabelClass.LANDFORM]: style(CartographicLabelClass.LANDFORM, { priority: 320, minZoom: 1.65, fontSizePx: 11, maxFontSizePx: 15, fontWeight: 650 }),
});

export function resolveCartographicStyle(labelClass, zoom = 1) {
  const key = String(labelClass ?? "").trim().toUpperCase();
  const base = CARTOGRAPHIC_STYLES[key];
  if (!base) throw new Error(`cartographic style is not defined for ${key || "unknown"}`);
  const z = Number(zoom);
  if (!Number.isFinite(z) || z <= 0) throw new RangeError("zoom must be a positive finite number");
  const eligible = z >= base.minZoom && z <= base.maxZoom;
  const scaled = Math.min(base.maxFontSizePx, base.fontSizePx * (1 + Math.max(0, z - 1) * base.fontScalePerZoom));
  return Object.freeze({ ...base, eligible, zoom: z, resolvedFontSizePx: Number(scaled.toFixed(3)) });
}

export function renderCartographicText(displayName, resolvedStyle) {
  const value = String(displayName ?? "").trim();
  if (!value) throw new TypeError("displayName is required");
  if (!resolvedStyle) throw new TypeError("resolvedStyle is required");
  if (resolvedStyle.textTransform === "uppercase") return value.toLocaleUpperCase("en");
  if (resolvedStyle.textTransform === "lowercase") return value.toLocaleLowerCase("en");
  return value;
}
