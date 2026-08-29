/** P006.7.11.15.7.3 — additive CITY geometry + label canvas above the REGION overlay. */
import { MapFitMode } from "../presentation/contracts.js";
import { createViewport, geographicToViewport } from "../presentation/viewport.js";
import { createCartographicLabelPlan } from "./label-plan.js";
import { renderCartographicLabels } from "./label-renderer.js";
import {
  assertPublishedNoveGeoCitySubset,
  createNoveGeoCityLabelCandidates,
  isNoveGeoCityMapItem,
} from "./city-anchor.js";

const DEFAULT_WIDTH = 640;
const MIN_WIDTH = 280;
const MIN_HEIGHT = 260;
const ASPECT = 0.68;
const ROLE = "novegeo-city-cartographic-canvas";

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
  if (!Array.isArray(value) || value.length < 2) throw new TypeError("CITY geometry coordinate must be [longitude,latitude]");
  const longitude = Number(value[0]);
  const latitude = Number(value[1]);
  if (!Number.isFinite(longitude) || !Number.isFinite(latitude)) throw new TypeError("CITY geometry coordinates must be finite");
  if (longitude < -180 || longitude > 180 || latitude < -90 || latitude > 90) throw new RangeError("CITY geometry coordinate outside EPSG:4326 bounds");
  return Object.freeze({ longitude, latitude });
}

export function normalizeCityPolygons(geometry) {
  if (!geometry || typeof geometry !== "object") throw new TypeError("CITY geometry is required");
  if (geometry.type === "Polygon") return Object.freeze([geometry.coordinates]);
  if (geometry.type === "MultiPolygon") return Object.freeze([...geometry.coordinates]);
  throw new Error(`unsupported CITY geometry type: ${geometry.type || "unknown"}`);
}

function drawCityPath(context, item, project) {
  const polygons = normalizeCityPolygons(item.geometry);
  let ringCount = 0;
  context.beginPath();
  for (const polygon of polygons) {
    if (!Array.isArray(polygon) || polygon.length < 1) throw new Error("CITY polygon requires at least one ring");
    for (const ring of polygon) {
      if (!Array.isArray(ring) || ring.length < 4) throw new Error("CITY ring requires at least four coordinates");
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

export function mountNoveGeoCityCartographicOverlay(documentRef, {
  boundaryPublication,
  cityItems = [],
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
  const officialCities = assertPublishedNoveGeoCitySubset(cityItems);

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
    zIndex: "4",
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
    if (!context) throw new Error("CITY cartographic overlay requires Canvas 2D");
    context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
    context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);

    const project = (longitude, latitude) => transformPoint(
      geographicToViewport(longitude, latitude, viewport), viewport, navigation
    );

    let polygonPartCount = 0;
    let ringCount = 0;
    context.save();
    context.fillStyle = "rgba(148,163,184,0.055)";
    context.strokeStyle = "rgba(226,232,240,0.94)";
    context.lineWidth = 1.5;
    context.lineJoin = "round";
    for (const item of officialCities) {
      if (!isNoveGeoCityMapItem(item)) continue;
      const receipt = drawCityPath(context, item, project);
      polygonPartCount += receipt.polygonPartCount;
      ringCount += receipt.ringCount;
    }
    context.restore();

    const candidates = createNoveGeoCityLabelCandidates(officialCities, { readRuntime });
    const labelPlan = createCartographicLabelPlan({ candidates, zoom: navigation.zoom, project });
    const labelReceipt = renderCartographicLabels({ context, plan: labelPlan });

    container.dataset.novegeoCityCartographyVersion = "1";
    container.dataset.novegeoCityCartographyStatus = "RENDERED";
    container.dataset.novegeoCityCount = String(officialCities.length);
    container.dataset.novegeoCityLabelCount = String(labelReceipt.renderedCount);

    latestReceipt = Object.freeze({
      status: "RENDERED",
      overlayVersion: 1,
      cityCount: officialCities.length,
      renderedCityIds: Object.freeze(officialCities.map((item) => item.subjectId)),
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
        delete container.dataset.novegeoCityCartographyVersion;
        delete container.dataset.novegeoCityCartographyStatus;
        delete container.dataset.novegeoCityCount;
        delete container.dataset.novegeoCityLabelCount;
      }
    },
  });
}
