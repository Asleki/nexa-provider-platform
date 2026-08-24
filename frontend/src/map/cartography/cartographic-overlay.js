/** P006.7.11.15.4 — additive national cartographic overlay above locked map canvases. */
import { MapFitMode } from "../presentation/contracts.js";
import { createViewport, geographicToViewport } from "../presentation/viewport.js";
import { createNoveGeoCountryLabelCandidate } from "./country-anchor.js";
import { createCartographicLabelPlan } from "./label-plan.js";
import { renderCartographicLabels } from "./label-renderer.js";

const DEFAULT_WIDTH = 640;
const MIN_WIDTH = 280;
const MIN_HEIGHT = 260;
const ASPECT = 0.68;
const ROLE = "novegeo-cartographic-label-canvas";

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

export function mountNoveGeoCartographicOverlay(documentRef, {
  boundaryPublication,
  countryId = "country:novegeo",
  countryName = "NoveGeo",
  devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
  observeResize = true,
  observeNavigation = true,
} = {}) {
  const container = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  const base = container?.querySelector?.("[data-role='novegeo-map-canvas']");
  if (!container || !base || typeof documentRef?.createElement !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "map_canvas_unavailable", disconnect() {} });
  }
  if (!boundaryPublication) throw new TypeError("boundaryPublication is required");

  let canvas = container.querySelector?.(`[data-role='${ROLE}']`);
  if (!canvas) {
    canvas = documentRef.createElement("canvas");
    canvas.setAttribute("data-role", ROLE);
    canvas.setAttribute("aria-hidden", "true");
    container.appendChild?.(canvas);
  }
  if (container.style) container.style.position = "relative";
  Object.assign(canvas.style || {}, { position: "absolute", inset: "0", zIndex: "4", pointerEvents: "none", transform: "none" });

  const candidate = createNoveGeoCountryLabelCandidate(boundaryPublication, { countryId, displayName: countryName });
  let latestReceipt = null;
  let disconnected = false;

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
    if (!context) throw new Error("cartographic overlay requires Canvas 2D");
    context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
    context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);
    const plan = createCartographicLabelPlan({
      candidates: [candidate],
      zoom: navigation.zoom,
      project: (longitude, latitude) => transformPoint(geographicToViewport(longitude, latitude, viewport), viewport, navigation),
    });
    const receipt = renderCartographicLabels({ context, plan });
    container.dataset.cartographyVersion = "1";
    container.dataset.cartographyStatus = receipt.status;
    container.dataset.cartographyLabelCount = String(receipt.renderedCount);
    latestReceipt = Object.freeze({
      ...receipt,
      countryId,
      countryName,
      anchorKind: candidate.anchor.kind,
      sourceBoundaryId: candidate.anchor.sourceBoundaryId,
      sourceBoundaryVersion: candidate.anchor.sourceBoundaryVersion,
      anchorAlgorithmId: candidate.anchor.algorithmId,
      anchorAlgorithmVersion: candidate.anchor.algorithmVersion,
      zoom: navigation.zoom,
      navigationOffsetX: navigation.offsetX,
      navigationOffsetY: navigation.offsetY,
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
    navigationObserver.observe(container, { attributes: true, attributeFilter: ["data-map-zoom", "data-map-navigation-revision"] });
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
        delete container.dataset.cartographyStatus;
        delete container.dataset.cartographyLabelCount;
      }
    },
  });
}
