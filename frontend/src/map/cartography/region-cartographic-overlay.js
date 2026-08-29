/** P006.7.11.15.6.2 — additive REGION geometry + label canvas above the locked sovereign canvas. */
import { MapFitMode } from "../presentation/contracts.js";
import { createViewport, geographicToViewport } from "../presentation/viewport.js";
import { createCartographicLabelPlan } from "./label-plan.js";
import { renderCartographicLabels } from "./label-renderer.js";
import {
  assertOfficialNoveGeoRegionSet,
  createNoveGeoRegionLabelCandidates,
  isNoveGeoRegionMapItem,
} from "./region-anchor.js";

const DEFAULT_WIDTH = 640;
const MIN_WIDTH = 280;
const MIN_HEIGHT = 260;
const ASPECT = 0.68;
const ROLE = "novegeo-region-cartographic-canvas";

function widthOf(container) {
  const rect = container.getBoundingClientRect?.();
  const width = Number(rect?.width || container.clientWidth || DEFAULT_WIDTH);
  return Number.isFinite(width) && width > 0 ? Math.max(MIN_WIDTH, width) : DEFAULT_WIDTH;
}
function heightOf(width) { return Math.max(MIN_HEIGHT, Math.round(width * ASPECT)); }

function navigationOf(container, base) {
  const fallbackZoom = Number(container.dataset?.mapZoom || 1);
  const text = String(base?.style?.transform || "");
  const match = text.match(/translate\(\s*(-?[\d.]+)px\s*,\s*(-?[\d.]+)px\s*\)\s*scale\(\s*([\d.]+)\s*\)/);
  if (match) return Object.freeze({ offsetX: Number(match[1]), offsetY: Number(match[2]), zoom: Number(match[3]) });
  return Object.freeze({ offsetX: 0, offsetY: 0, zoom: Number.isFinite(fallbackZoom) && fallbackZoom > 0 ? fallbackZoom : 1 });
}

function transformPoint(point, viewport, navigation) {
  const centerX = viewport.cssWidth / 2;
  const centerY = viewport.cssHeight / 2;
  return Object.freeze({
    x: centerX + (point.x - centerX) * navigation.zoom + navigation.offsetX,
    y: centerY + (point.y - centerY) * navigation.zoom + navigation.offsetY,
  });
}

function coordinatePoint(value) {
  if (!Array.isArray(value) || value.length < 2) throw new TypeError("REGION geometry coordinate must be [longitude,latitude]");
  const longitude = Number(value[0]);
  const latitude = Number(value[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) throw new TypeError("REGION geometry coordinates must be finite");
  if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) throw new RangeError("REGION geometry coordinate outside EPSG:4326 bounds");
  return Object.freeze({ longitude, latitude });
}

export function normalizeRegionPolygons(geometry) {
  if (!geometry || typeof geometry !== "object") throw new TypeError("REGION geometry is required");
  if (geometry.type === "Polygon") return Object.freeze([geometry.coordinates]);
  if (geometry.type === "MultiPolygon") return Object.freeze([...geometry.coordinates]);
  throw new Error(`unsupported REGION geometry type: ${geometry.type || "unknown"}`);
}

function drawRegionPath(context, item, project) {
  const polygons = normalizeRegionPolygons(item.geometry);
  let ringCount = 0;
  context.beginPath();
  for (const polygon of polygons) {
    if (!Array.isArray(polygon) || polygon.length < 1) throw new Error("REGION polygon requires at least one ring");
    for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) throw new Error("REGION ring requires at least four coordinates");
      ring.forEach((coordinate, index) => {
        const geographic = coordinatePoint(coordinate);
        const point = project(geographic.longitude, geographic.latitude);
        if (index === 0) context.moveTo(point.x, point.y);
        else context.lineTo(point.x, point.y);
      });
      context.closePath();
      ringCount += 1;
    }
  }
  context.fill("evenodd");
  context.stroke();
  return Object.freeze({ polygonPartCount: polygons.length, ringCount });
}

export function mountNoveGeoRegionCartographicOverlay(documentRef, {
  boundaryPublication,
  regionItems = [],
  readRuntime = "simulation",
  devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
  observeResize = true,
  observeNavigation = true,
} = {}) {
  const container = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  const base = container?.querySelector?.("[data-role='novegeo-map-canvas']");
  if (!container || !base || typeof documentRef?.createElement !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "map_canvas_unavailable", disconnect() {} });
  }
  if (!boundaryPublication?.extent) throw new TypeError("boundaryPublication with extent is required");
  const officialRegions = assertOfficialNoveGeoRegionSet(regionItems);

  let canvas = container.querySelector?.(`[data-role='${ROLE}']`);
  if (!canvas) {
    canvas = documentRef.createElement("canvas");
    canvas.setAttribute("data-role", ROLE);
    canvas.setAttribute("aria-hidden", "true");
    container.appendChild?.(canvas);
  }
  if (container.style) container.style.position = "relative";
  Object.assign(canvas.style || {}, {
    position: "absolute",
    inset: "0",
    zIndex: "3",
    pointerEvents: "none",
    transform: "none",
  });

  let disconnected = false;
  let latestReceipt = null;

  const render = () => {
    if (disconnected) return Object.freeze({ status: "DISCONNECTED" });
    const width = widthOf(container);
    const height = heightOf(width);
    const viewport = createViewport({
      cssWidth: width,
      cssHeight: height,
      devicePixelRatio,
      padding: Math.min(36, Math.max(20, width * 0.055)),
      fitMode: MapFitMode.BOUNDARY,
      extent: boundaryPublication.extent,
    });
    const navigation = navigationOf(container, base);
    canvas.width = viewport.renderWidth;
    canvas.height = viewport.renderHeight;
    Object.assign(canvas.style || {}, { width: `${viewport.cssWidth}px`, height: `${viewport.cssHeight}px` });
    const context = canvas.getContext?.("2d");
    if (!context) throw new Error("REGION cartographic overlay requires Canvas 2D");
    context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
    context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);

    const project = (longitude, latitude) => transformPoint(
      geographicToViewport(longitude, latitude, viewport), viewport, navigation
    );

    let polygonPartCount = 0;
    let ringCount = 0;
    context.save();
    context.fillStyle = "rgba(248,250,252,0.045)";
    context.strokeStyle = "rgba(226,232,240,0.82)";
    context.lineWidth = 1.25;
    context.lineJoin = "round";
    for (const item of officialRegions) {
      if (!isNoveGeoRegionMapItem(item)) continue;
      const receipt = drawRegionPath(context, item, project);
      polygonPartCount += receipt.polygonPartCount;
      ringCount += receipt.ringCount;
    }
    context.restore();

    const candidates = createNoveGeoRegionLabelCandidates(officialRegions, { readRuntime });
    const labelPlan = createCartographicLabelPlan({ candidates, zoom: navigation.zoom, project });
    const labelReceipt = renderCartographicLabels({ context, plan: labelPlan });

    container.dataset.novegeoRegionCartographyVersion = "1";
    container.dataset.novegeoRegionCartographyStatus = "RENDERED";
    container.dataset.novegeoRegionCount = String(officialRegions.length);
    container.dataset.novegeoRegionLabelCount = String(labelReceipt.renderedCount);

    latestReceipt = Object.freeze({
      status: "RENDERED",
      overlayVersion: 1,
      regionCount: officialRegions.length,
      renderedRegionIds: Object.freeze(officialRegions.map((item) => item.subjectId)),
      polygonPartCount,
      ringCount,
      labelCandidateCount: candidates.length,
      labelPlanCount: labelPlan.labels.length,
      labelRenderedCount: labelReceipt.renderedCount,
      labelCollisionRejectedCount: labelReceipt.collisionRejectedCount,
      renderedLabelSubjectIds: labelReceipt.renderedSubjectIds,
      readRuntime,
      zoom: navigation.zoom,
      navigationOffsetX: navigation.offsetX,
      navigationOffsetY: navigation.offsetY,
      viewportId: viewport.viewportId,
      viewportVersion: viewport.viewportVersion,
    });
    return latestReceipt;
  };

  const firstReceipt = render();
  let resizeObserver = null;
  let navigationObserver = null;
  if (observeResize && typeof globalThis.ResizeObserver === "function") {
    resizeObserver = new globalThis.ResizeObserver(() => { if (!disconnected) render(); });
    resizeObserver.observe(container);
  }
  if (observeNavigation && typeof globalThis.MutationObserver === "function") {
    navigationObserver = new globalThis.MutationObserver(() => { if (!disconnected) render(); });
    navigationObserver.observe(container, {
      attributes: true,
      attributeFilter: ["data-map-zoom", "data-map-navigation-revision"],
    });
  }

  return Object.freeze({
    status: firstReceipt.status,
    firstReceipt,
    get latestReceipt() { return latestReceipt; },
    redraw: render,
    disconnect() {
      disconnected = true;
      resizeObserver?.disconnect();
      navigationObserver?.disconnect();
      canvas.remove?.();
      if (container.dataset) {
        delete container.dataset.novegeoRegionCartographyVersion;
        delete container.dataset.novegeoRegionCartographyStatus;
        delete container.dataset.novegeoRegionCount;
        delete container.dataset.novegeoRegionLabelCount;
      }
    },
  });
}
