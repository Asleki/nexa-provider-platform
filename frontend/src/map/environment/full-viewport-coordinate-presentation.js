/**
 * Bundle 11.0C — additive full-viewport geographic reference presentation.
 * Extends the locked P004 graticule/equator visually to the map-frame edges
 * without changing the governed CRS, boundary geometry, coordinate values, or P004 renderer.
 */
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../presentation/publication.js";
import { MapFitMode } from "../presentation/contracts.js";
import { createViewport } from "../presentation/viewport.js";
import { createCoordinateGrid } from "../presentation/coordinate-grid.js";

const DEFAULT_VIEWPORT_WIDTH = 640;
const MINIMUM_VIEWPORT_WIDTH = 280;
const MINIMUM_VIEWPORT_HEIGHT = 260;
const VIEWPORT_ASPECT_RATIO = 0.68;
const COORDINATE_OVERLAY_Z_INDEX = "3";
const GRID_STROKE = "rgba(203, 213, 225, 0.24)";
const EQUATOR_STROKE = "#19d3e6";

function widthOf(container) {
  const rect = typeof container.getBoundingClientRect === "function" ? container.getBoundingClientRect() : null;
  const measured = Number(rect?.width || container.clientWidth || DEFAULT_VIEWPORT_WIDTH);
  return Number.isFinite(measured) && measured > 0 ? Math.max(MINIMUM_VIEWPORT_WIDTH, measured) : DEFAULT_VIEWPORT_WIDTH;
}

function heightOf(width) {
  return Math.max(MINIMUM_VIEWPORT_HEIGHT, Math.round(width * VIEWPORT_ASPECT_RATIO));
}

function extendLineToFrame(line, viewport) {
  if (line.type === "longitude") {
    return Object.freeze({ ...line, start: Object.freeze({ ...line.start, y: 0 }), end: Object.freeze({ ...line.end, y: viewport.cssHeight }) });
  }
  return Object.freeze({ ...line, start: Object.freeze({ ...line.start, x: 0 }), end: Object.freeze({ ...line.end, x: viewport.cssWidth }) });
}

export function createFullViewportCoordinatePlan(viewport, options = {}) {
  const grid = createCoordinateGrid(viewport, options);
  return Object.freeze({
    overlayId: "overlay:novegeo:full-viewport-coordinate-presentation",
    overlayVersion: 1,
    longitudeLines: Object.freeze(grid.longitudeLines.map((line) => extendLineToFrame(line, viewport))),
    latitudeLines: Object.freeze(grid.latitudeLines.map((line) => extendLineToFrame(line, viewport))),
    equator: grid.equator ? extendLineToFrame(grid.equator, viewport) : null,
  });
}

function drawLine(context, line) {
  context.beginPath();
  context.moveTo(line.start.x, line.start.y);
  context.lineTo(line.end.x, line.end.y);
  context.stroke();
}

export function renderFullViewportCoordinateCanvas({ canvas, viewport, plan }) {
  const context = canvas?.getContext?.("2d");
  if (!context) throw new Error("full-viewport coordinate canvas requires Canvas 2D");

  canvas.width = viewport.renderWidth;
  canvas.height = viewport.renderHeight;
  Object.assign(canvas.style || {}, {
    width: `${viewport.cssWidth}px`,
    height: `${viewport.cssHeight}px`,
    position: "absolute",
    inset: "0",
    zIndex: COORDINATE_OVERLAY_Z_INDEX,
    pointerEvents: "none",
  });

  context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
  context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);

  context.save();
  context.strokeStyle = GRID_STROKE;
  context.lineWidth = 1;
  for (const line of [...plan.longitudeLines, ...plan.latitudeLines]) drawLine(context, line);
  context.restore();

  if (plan.equator) {
    context.save();
    context.strokeStyle = EQUATOR_STROKE;
    context.lineWidth = 2;
    context.setLineDash([7, 5]);
    drawLine(context, plan.equator);
    context.restore();
  }

  return Object.freeze({
    status: "RENDERED",
    overlayId: plan.overlayId,
    overlayVersion: plan.overlayVersion,
    longitudeLineCount: plan.longitudeLines.length,
    latitudeLineCount: plan.latitudeLines.length,
    equatorRendered: Boolean(plan.equator),
    frameCoverage: "full_viewport",
  });
}

export function mountFullViewportCoordinatePresentation(documentRef, {
  boundaryPublication = BUNDLED_WORLD_BOUNDARY_PUBLICATION,
  devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
  longitudeInterval = 5,
  latitudeInterval = 5,
} = {}) {
  const container = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  if (!container || typeof documentRef?.createElement !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "viewport_missing" });
  }

  const boundaryCanvas = container.querySelector?.("[data-role='novegeo-map-canvas']");
  if (!boundaryCanvas) return Object.freeze({ status: "UNAVAILABLE", reason: "boundary_canvas_missing" });

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
  const plan = createFullViewportCoordinatePlan(viewport, { longitudeInterval, latitudeInterval });

  const existingCanvas = container.querySelector?.("[data-role='novegeo-full-viewport-coordinate-canvas']");
  const canvas = existingCanvas || documentRef.createElement("canvas");
  canvas.setAttribute("data-role", "novegeo-full-viewport-coordinate-canvas");
  canvas.setAttribute("aria-hidden", "true");
  if (container.style) container.style.position = "relative";
  if (!existingCanvas) {
    if (typeof container.appendChild === "function") container.appendChild(canvas);
  }

  return renderFullViewportCoordinateCanvas({ canvas, viewport, plan });
}
