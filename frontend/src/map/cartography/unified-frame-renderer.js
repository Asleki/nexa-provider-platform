/** P006.7.11.15.10 — one unified map-first frame renderer. */
import {
  createUniformProjectedViewport,
  geographicToUnifiedViewport,
  geographicToNavigatedViewport,
  viewportPointToGeographic,
} from "./unified-projection.js";
import { createGeodesicScaleModel } from "./geodesic-scale-v2.js";
import { createUnifiedFramePlan, declutterUnifiedLabels } from "./unified-frame-plan.js";
import { renderUnifiedEnvironmentalComposition } from "./unified-environmental-compositor.js";
import { UnifiedLayerKey } from "./semantic-zoom-v2.js";

export const UNIFIED_CANVAS_ROLE = "novegeo-unified-cartographic-canvas";
export const UNIFIED_RENDERER_VERSION = 2;

const LAYER_DRAW_STYLE = Object.freeze({
  [UnifiedLayerKey.REGION]: Object.freeze({ fill: "rgba(96,165,250,0.025)", stroke: "rgba(191,219,254,0.62)", width: 1.15, dash: [] }),
  [UnifiedLayerKey.CITY]: Object.freeze({ fill: "rgba(226,232,240,0.035)", stroke: "rgba(241,245,249,0.72)", width: 1.05, dash: [] }),
  [UnifiedLayerKey.MUNICIPALITY]: Object.freeze({ fill: "rgba(94,234,212,0.025)", stroke: "rgba(153,246,228,0.52)", width: 0.95, dash: [4, 3] }),
  [UnifiedLayerKey.CITY_DISTRICT]: Object.freeze({ fill: "rgba(203,213,225,0.018)", stroke: "rgba(203,213,225,0.42)", width: 0.8, dash: [2, 3] }),
});

function coordinate(value) {
  if (!Array.isArray(value) || value.length < 2) throw new TypeError("GeoJSON coordinate must contain longitude and latitude");
  const longitude = Number(value[0]);
  const latitude = Number(value[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) throw new TypeError("GeoJSON coordinates must be finite");
  return { longitude, latitude };
}

export function normalizePolygonGeometry(geometry) {
  if (!geometry || typeof geometry !== "object") throw new TypeError("polygon geometry is required");
  if (geometry.type === "Polygon") return Object.freeze([geometry.coordinates]);
  if (geometry.type === "MultiPolygon") return Object.freeze([...geometry.coordinates]);
  throw new Error(`unsupported polygon geometry type: ${geometry.type || "unknown"}`);
}

function traceGeometry(context, geometry, project) {
  const polygons = normalizePolygonGeometry(geometry);
  context.beginPath();
  let ringCount = 0;
  for (const polygon of polygons) {
    for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) throw new Error("polygon ring requires at least four coordinates");
      ring.forEach((value, index) => {
        const geographic = coordinate(value);
        const point = project(geographic.longitude, geographic.latitude);
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.closePath();
      ringCount += 1;
    }
  }
  return Object.freeze({ polygonPartCount: polygons.length, ringCount });
}

function drawBoundary(context, boundaryPublication, project) {
  context.save();
  traceGeometry(context, boundaryPublication.geometry, project);
  context.fillStyle = "rgba(30,64,175,0.26)";
  context.strokeStyle = "rgba(248,250,252,0.88)";
  context.lineWidth = 1.5;
  context.lineJoin = "round";
  context.fill("evenodd");
  context.stroke();
  context.restore();
}

function drawEquatorReference(context, boundaryPublication, project, enabled) {
  if (!enabled) return false;
  const extent = boundaryPublication.extent;
  if (Number(extent.minLatitude) > 0 || Number(extent.maxLatitude) < 0) return false;
  const start = project(extent.minLongitude, 0);
  const end = project(extent.maxLongitude, 0);
  context.save();
  context.beginPath();
  context.moveTo(start.x, start.y);
  context.lineTo(end.x, end.y);
  context.setLineDash([6, 6]);
  context.strokeStyle = "rgba(103,232,249,0.34)";
  context.lineWidth = 0.8;
  context.stroke();
  context.restore();
  return true;
}

function drawAdministrativeGeometry(context, records, project) {
  const counts = {};
  for (const record of records) {
    const style = LAYER_DRAW_STYLE[record.layerKey];
    if (!style || !record.geometry) continue;
    context.save();
    context.fillStyle = style.fill;
    context.strokeStyle = style.stroke;
    context.lineWidth = style.width;
    context.lineJoin = "round";
    context.setLineDash(style.dash);
    traceGeometry(context, record.geometry, project);
    context.fill("evenodd");
    context.stroke();
    context.restore();
    counts[record.layerKey] = (counts[record.layerKey] || 0) + 1;
  }
  return Object.freeze({ ...counts });
}

function drawSettlementSymbols(context, symbols) {
  for (const symbol of symbols) {
    context.save();
    context.beginPath();
    context.arc(symbol.x, symbol.y, symbol.style.radiusPx, 0, Math.PI * 2);
    context.fillStyle = symbol.style.fillStyle;
    context.strokeStyle = symbol.style.strokeStyle;
    context.lineWidth = symbol.style.strokeWidthPx;
    context.fill();
    context.stroke();
    context.restore();
  }
}

function font(style) {
  return `${style.fontWeight} ${style.fontSizePx}px ${style.fontFamily}`;
}

function measureLabel(context, label) {
  context.save();
  context.font = font(label.style);
  const width = context.measureText(label.renderedText).width;
  context.restore();
  return Object.freeze({ width, height: label.style.fontSizePx * 1.22 });
}

function resolveLabelCollision(context, labels, symbols) {
  const measured = labels.map((label) => Object.freeze({ label, metrics: measureLabel(context, label) }));
  return declutterUnifiedLabels(measured, symbols);
}

function drawLabels(context, acceptedLabels) {
  for (const item of acceptedLabels) {
    const label = item.label;
    context.save();
    context.font = font(label.style);
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.lineJoin = "round";
    context.strokeStyle = label.style.haloStyle;
    context.fillStyle = label.style.fillStyle;
    context.lineWidth = label.style.haloWidthPx * 2;
    if (label.style.haloWidthPx > 0) context.strokeText(label.renderedText, label.x, label.y);
    context.fillText(label.renderedText, label.x, label.y);
    context.restore();
  }
}

function presentationTargetReceipts(plan, collision) {
  const acceptedLabelIds = new Set(collision.accepted.map((item) => item.label.subjectId));
  const acceptedSymbolIds = new Set(collision.acceptedSymbols.map((symbol) => symbol.subjectId));
  const rejectedLabelReason = new Map(collision.rejected.map((item) => [item.label.subjectId, item.reason]));
  const rejectedSymbolReason = new Map(collision.rejectedSymbols.map((item) => [item.symbol.subjectId, item.reason]));
  return Object.freeze(plan.presentationTargets.map((target) => Object.freeze({
    ...target,
    labelRendered: acceptedLabelIds.has(target.subjectId),
    symbolRendered: acceptedSymbolIds.has(target.subjectId),
    labelRejectedReason: rejectedLabelReason.get(target.subjectId) || null,
    symbolRejectedReason: rejectedSymbolReason.get(target.subjectId) || null,
  })));
}

function configureCanvas(canvas, viewport) {
  const context = canvas?.getContext?.("2d");
  if (!context) throw new Error("unified map presentation requires Canvas 2D");
  canvas.width = viewport.renderWidth;
  canvas.height = viewport.renderHeight;
  Object.assign(canvas.style || {}, {
    width: `${viewport.cssWidth}px`,
    height: `${viewport.cssHeight}px`,
    position: "absolute",
    inset: "0",
    zIndex: "12",
    pointerEvents: "none",
  });
  context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
  context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);
  return context;
}

export function renderUnifiedCartographicFrame({
  canvas,
  cssWidth,
  cssHeight,
  devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
  boundaryPublication,
  countryCandidate,
  snapshots,
  zoom,
  navigation,
  previousBand = null,
  userLayerVisibility = {},
  environmentalLayerVisibility = {},
  presentationRoles = {},
  preserveGeographicCenter = null,
} = {}) {
  const width = Number(cssWidth);
  const height = Number(cssHeight);
  if (!Number.isFinite(width) || width <= 0 || !Number.isFinite(height) || height <= 0) {
    throw new RangeError("unified frame requires positive viewport dimensions");
  }
  const padding = Math.min(36, Math.max(16, Math.min(width, height) * 0.045));
  const viewport = createUniformProjectedViewport({
    cssWidth: width,
    cssHeight: height,
    devicePixelRatio,
    padding,
    extent: boundaryPublication.extent,
  });
  let effectiveNavigation = Object.freeze({
    zoom: Number(navigation?.zoom || 1),
    offsetX: Number(navigation?.offsetX || 0),
    offsetY: Number(navigation?.offsetY || 0),
  });
  if (preserveGeographicCenter) {
    const centrePoint = geographicToUnifiedViewport(
      Number(preserveGeographicCenter.longitude),
      Number(preserveGeographicCenter.latitude),
      viewport,
    );
    const centreX = viewport.cssWidth / 2;
    const centreY = viewport.cssHeight / 2;
    effectiveNavigation = Object.freeze({
      zoom: effectiveNavigation.zoom,
      offsetX: -(centrePoint.x - centreX) * effectiveNavigation.zoom,
      offsetY: -(centrePoint.y - centreY) * effectiveNavigation.zoom,
    });
  }
  const project = (longitude, latitude) => geographicToNavigatedViewport(longitude, latitude, viewport, effectiveNavigation);
  const plan = createUnifiedFramePlan({
    boundaryPublication,
    countryCandidate,
    snapshots,
    zoom,
    previousBand,
    userLayerVisibility,
    project,
    presentationRoles,
  });
  const context = configureCanvas(canvas, viewport);

  context.save();
  context.fillStyle = "#07111f";
  context.fillRect(0, 0, viewport.cssWidth, viewport.cssHeight);
  context.restore();

  const environment = renderUnifiedEnvironmentalComposition({
    context,
    cssWidth: viewport.cssWidth,
    cssHeight: viewport.cssHeight,
    boundaryPublication,
    project,
    layerVisibility: environmentalLayerVisibility,
  });
  drawBoundary(context, boundaryPublication, project);
  const geometryCounts = drawAdministrativeGeometry(context, plan.geometry, project);
  const collision = resolveLabelCollision(context, plan.labels, plan.symbols);
  const presentationTargets = presentationTargetReceipts(plan, collision);
  drawSettlementSymbols(context, collision.acceptedSymbols);
  drawLabels(context, collision.accepted);
  const scale = createGeodesicScaleModel({ viewport, navigation: effectiveNavigation });

  const geographicCenter = viewportPointToGeographic(
    viewport.cssWidth / 2,
    viewport.cssHeight / 2,
    viewport,
    effectiveNavigation,
  );

  const visible = new Set();
  for (const record of plan.geometry) if (record.subjectId) visible.add(record.subjectId);
  for (const symbol of collision.acceptedSymbols) visible.add(symbol.subjectId);
  for (const item of collision.accepted) visible.add(item.label.subjectId);

  return Object.freeze({
    status: "RENDERED",
    rendererVersion: UNIFIED_RENDERER_VERSION,
    planId: plan.planId,
    planVersion: plan.planVersion,
    semanticBand: plan.semanticBand,
    sourceCandidateCount: plan.sourceCandidateCount,
    publicationEligibleCount: plan.publicationEligibleCount,
    zoomEligibleCount: plan.zoomEligibleCount,
    collisionAcceptedCount: collision.accepted.length,
    collisionRejectedCount: collision.rejected.length,
    visibleSubjectIds: Object.freeze([...visible].sort()),
    collisionRejectedSubjectIds: Object.freeze(collision.rejected.map((item) => item.label.subjectId).sort()),
    settlementSymbolCandidateCount: plan.symbols.length,
    settlementSymbolCount: collision.acceptedSymbols.length,
    settlementSymbolRejectedSubjectIds: Object.freeze(collision.rejectedSymbols.map((item) => item.symbol.subjectId).sort()),
    presentationTargets,
    geometryFeatureCount: plan.geometry.length,
    geometryCounts,
    equatorRendered: environment.equatorRendered,
    environment,
    scale,
    geographicCenter: Object.freeze({
      longitude: geographicCenter.longitude,
      latitude: geographicCenter.latitude,
    }),
    navigationUsed: effectiveNavigation,
    viewport: Object.freeze({
      cssWidth: viewport.cssWidth,
      cssHeight: viewport.cssHeight,
      uniformScale: viewport.uniformScale,
      widthScale: viewport.widthScale,
      heightScale: viewport.heightScale,
      fittedWidth: viewport.fittedWidth,
      fittedHeight: viewport.fittedHeight,
    }),
  });
}
