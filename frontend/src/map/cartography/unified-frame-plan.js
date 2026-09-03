/** P006.7.11.15.10 — deterministic unified geometry/symbol/label frame planning. */
import {
  resolveSemanticZoomBand,
  semanticLayerVisibility,
  layerKeyForLabelClass,
  resolveUnifiedLabelStyle,
  settlementSymbolStyle,
  UnifiedLayerKey,
} from "./semantic-zoom-v2.js";

export const UNIFIED_FRAME_PLAN_ID = "render-plan:novegeo:map-first-unified";
export const UNIFIED_FRAME_PLAN_VERSION = 1;

const REQUIRED_LAYER_KEYS = Object.freeze([
  UnifiedLayerKey.REGION,
  UnifiedLayerKey.CITY,
  UnifiedLayerKey.MUNICIPALITY,
  UnifiedLayerKey.CITY_DISTRICT,
  UnifiedLayerKey.TOWN,
]);

export { REQUIRED_LAYER_KEYS };

function enabled(visibility, layerKey) {
  return visibility?.[layerKey] !== false;
}

function candidateRecord(candidate, layerKey, publicationEligible = true, presentationRole = null) {
  if (!candidate || typeof candidate !== "object") throw new TypeError("label candidate must be an object");
  if (!candidate.subjectId || !candidate.displayName || !candidate.anchor) throw new TypeError("label candidate is incomplete");
  return Object.freeze({ candidate, layerKey, publicationEligible, presentationRole });
}

function referenceCandidate(boundaryPublication) {
  const extent = boundaryPublication?.extent;
  if (!extent || Number(extent.minLatitude) > 0 || Number(extent.maxLatitude) < 0) return null;
  return Object.freeze({
    subjectId: "reference:novegeo:equator",
    displayName: "Equator · 0°",
    labelClass: "REFERENCE",
    anchor: Object.freeze({
      longitude: Number(extent.minLongitude) + (Number(extent.maxLongitude) - Number(extent.minLongitude)) * 0.12,
      latitude: 0,
    }),
    runtimeMode: "shared_reference",
    publicationReference: null,
  });
}

function geometryRecord(layerKey, item) {
  return Object.freeze({
    layerKey,
    subjectId: String(item?.subjectId || ""),
    geometry: item?.geometry || null,
  });
}

export function createUnifiedFramePlan({
  boundaryPublication,
  countryCandidate,
  snapshots = {},
  zoom = 1,
  previousBand = null,
  userLayerVisibility = {},
  project,
  presentationRoles = {},
} = {}) {
  if (!boundaryPublication?.extent || !boundaryPublication?.geometry) throw new TypeError("boundaryPublication is required");
  if (!countryCandidate) throw new TypeError("countryCandidate is required");
  if (typeof project !== "function") throw new TypeError("project must be a function");

  const band = resolveSemanticZoomBand(zoom, previousBand);
  const records = [candidateRecord(countryCandidate, UnifiedLayerKey.COUNTRY, true, presentationRoles[countryCandidate.subjectId] || null)];

  for (const layerKey of REQUIRED_LAYER_KEYS) {
    const snapshot = snapshots[layerKey];
    if (!snapshot) continue;
    for (const candidate of snapshot.candidates || []) {
      records.push(candidateRecord(candidate, layerKey, true, presentationRoles[candidate.subjectId] || null));
    }
  }

  if (enabled(userLayerVisibility, UnifiedLayerKey.REFERENCE)) {
    const equator = referenceCandidate(boundaryPublication);
    if (equator) records.push(candidateRecord(equator, UnifiedLayerKey.REFERENCE, false, null));
  }

  const labels = [];
  const symbols = [];
  const geometry = [];

  for (const layerKey of REQUIRED_LAYER_KEYS) {
    const snapshot = snapshots[layerKey];
    if (!snapshot || !enabled(userLayerVisibility, layerKey)) continue;
    const visibility = semanticLayerVisibility(layerKey, zoom);
    if (visibility.geometry) {
      for (const item of snapshot.items || []) {
        if (item?.geometry) geometry.push(geometryRecord(layerKey, item));
      }
    }
  }

  for (const record of records) {
    if (!enabled(userLayerVisibility, record.layerKey)) continue;
    const semantic = semanticLayerVisibility(record.layerKey, zoom);
    if (semantic.symbol) {
      const symbolStyle = settlementSymbolStyle(record.layerKey, { presentationRole: record.presentationRole });
      if (symbolStyle) {
        const point = project(record.candidate.anchor.longitude, record.candidate.anchor.latitude);
        symbols.push(Object.freeze({
          subjectId: record.candidate.subjectId,
          layerKey: record.layerKey,
          presentationRole: record.presentationRole,
          x: Number(point.x),
          y: Number(point.y),
          style: symbolStyle,
        }));
      }
    }
    if (!semantic.label) continue;
    const style = resolveUnifiedLabelStyle(record.candidate.labelClass, { presentationRole: record.presentationRole });
    const point = project(record.candidate.anchor.longitude, record.candidate.anchor.latitude);
    labels.push(Object.freeze({
      subjectId: record.candidate.subjectId,
      layerKey: record.layerKey,
      labelClass: record.candidate.labelClass,
      displayName: record.candidate.displayName,
      renderedText: String(record.candidate.displayName),
      publicationReference: record.candidate.publicationReference || null,
      runtimeMode: record.candidate.runtimeMode || "shared_reference",
      x: Number(point.x) + Number(style.labelOffsetXPx || 0),
      y: Number(point.y) + Number(style.labelOffsetYPx || 0),
      priority: style.priority,
      style,
    }));
  }

  labels.sort((a, b) => b.priority - a.priority || a.layerKey.localeCompare(b.layerKey) || a.subjectId.localeCompare(b.subjectId));
  symbols.sort((a, b) => b.style.priority - a.style.priority || a.subjectId.localeCompare(b.subjectId));
  geometry.sort((a, b) => REQUIRED_LAYER_KEYS.indexOf(a.layerKey) - REQUIRED_LAYER_KEYS.indexOf(b.layerKey) || a.subjectId.localeCompare(b.subjectId));

  return Object.freeze({
    planId: UNIFIED_FRAME_PLAN_ID,
    planVersion: UNIFIED_FRAME_PLAN_VERSION,
    semanticBand: band,
    zoom: Number(zoom),
    sourceCandidateCount: records.length,
    publicationEligibleCount: records.filter((record) => record.publicationEligible).length,
    zoomEligibleCount: labels.length,
    geometry: Object.freeze(geometry),
    symbols: Object.freeze(symbols),
    labels: Object.freeze(labels),
  });
}

function overlaps(a, b) {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

function labelBox(label, metrics) {
  const width = Number(metrics?.width);
  const height = Number(metrics?.height);
  if (!Number.isFinite(width) || width < 0 || !Number.isFinite(height) || height <= 0) {
    throw new RangeError("label metrics must contain finite positive dimensions");
  }
  const padding = Number(label.style?.collisionPaddingPx || 0);
  return Object.freeze({
    left: label.x - width / 2 - padding,
    right: label.x + width / 2 + padding,
    top: label.y - height / 2 - padding,
    bottom: label.y + height / 2 + padding,
  });
}

function symbolBox(symbol) {
  const radius = Number(symbol.style.radiusPx || 0) + Number(symbol.style.clearancePx || 0);
  return Object.freeze({
    left: symbol.x - radius,
    right: symbol.x + radius,
    top: symbol.y - radius,
    bottom: symbol.y + radius,
  });
}

export function declutterUnifiedLabels(measuredLabels = [], symbols = []) {
  const accepted = [];
  const rejected = [];
  const symbolClearance = symbols.map((symbol) => Object.freeze({ symbol, box: symbolBox(symbol) }));
  const ordered = [...measuredLabels].sort((a, b) => b.label.priority - a.label.priority || a.label.subjectId.localeCompare(b.label.subjectId));
  for (const item of ordered) {
    const box = labelBox(item.label, item.metrics);
    const symbolConflict = symbolClearance.some(({ symbol, box: clearance }) => symbol.subjectId !== item.label.subjectId && overlaps(clearance, box));
    const labelConflict = accepted.some((existing) => overlaps(existing.box, box));
    if (symbolConflict || labelConflict) {
      rejected.push(Object.freeze({ ...item, box, reason: symbolConflict ? "settlement_symbol_clearance" : "label_collision" }));
    } else {
      accepted.push(Object.freeze({ ...item, box }));
    }
  }
  return Object.freeze({ accepted: Object.freeze(accepted), rejected: Object.freeze(rejected) });
}

export function layerKeyForCandidate(candidate) {
  return layerKeyForLabelClass(candidate?.labelClass);
}
