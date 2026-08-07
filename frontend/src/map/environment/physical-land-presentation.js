/**
 * P005.1/P005.2 additive physical-land presentation.
 * Composites governed terrain and semantic landform tint above the locked P004 canvas
 * while preserving P004 reference graphics through controlled transparency.
 */
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../presentation/publication.js";
import { createBoundaryRenderPlan } from "../presentation/boundary-render-plan.js";
import { createViewport } from "../presentation/viewport.js";
import { MapFitMode } from "../presentation/contracts.js";
import { NOVEGEO_TERRAIN_STANDARD } from "../terrain/catalog.js";
import { createTerrainRenderPlan } from "../terrain/render-plan.js";
import { NOVEGEO_LANDFORMS_STANDARD } from "../landforms/catalog.js";
import { createLandformRenderPlan } from "../landforms/render-plan.js";

const DEFAULT_VIEWPORT_WIDTH = 640;
const MINIMUM_VIEWPORT_WIDTH = 280;
const MINIMUM_VIEWPORT_HEIGHT = 260;
const VIEWPORT_ASPECT_RATIO = 0.68;
const PHYSICAL_LAND_Z_INDEX = "2";
const P004_MAP_Z_INDEX = "1";
const TERRAIN_COMPOSITE_ALPHA = 0.72;

function widthOf(container) {
  const rect = typeof container.getBoundingClientRect === "function" ? container.getBoundingClientRect() : null;
  const measured = Number(rect?.width || container.clientWidth || DEFAULT_VIEWPORT_WIDTH);
  return Number.isFinite(measured) && measured > 0 ? Math.max(MINIMUM_VIEWPORT_WIDTH, measured) : DEFAULT_VIEWPORT_WIDTH;
}

function heightOf(width) {
  return Math.max(MINIMUM_VIEWPORT_HEIGHT, Math.round(width * VIEWPORT_ASPECT_RATIO));
}

function boundaryClip(context, boundaryPlan) {
  context.beginPath();
  for (const polygon of boundaryPlan.polygons) {
    for (const ring of polygon.rings) {
      ring.points.forEach((point, index) => index === 0 ? context.moveTo(point.x, point.y) : context.lineTo(point.x, point.y));
      context.closePath();
    }
  }
  context.clip("evenodd");
}

export function renderPhysicalLandCanvas({ canvas, viewport, terrainPlan, landformPlan, boundaryPlan }) {
  const context = canvas?.getContext?.("2d");
  if (!context) throw new Error("physical-land canvas requires Canvas 2D");
  canvas.width = viewport.renderWidth;
  canvas.height = viewport.renderHeight;
  Object.assign(canvas.style || {}, {
    width: `${viewport.cssWidth}px`, height: `${viewport.cssHeight}px`, position: "absolute", inset: "0", zIndex: PHYSICAL_LAND_Z_INDEX, pointerEvents: "none",
  });
  context.setTransform(viewport.devicePixelRatio, 0, 0, viewport.devicePixelRatio, 0, 0);
  context.clearRect(0, 0, viewport.cssWidth, viewport.cssHeight);
  context.save();
  boundaryClip(context, boundaryPlan);
  context.save();
  context.globalAlpha = TERRAIN_COMPOSITE_ALPHA;
  for (const sample of terrainPlan.samples) {
    context.fillStyle = sample.color;
    context.fillRect(sample.x - terrainPlan.cellWidth / 2, sample.y - terrainPlan.cellHeight / 2, terrainPlan.cellWidth, terrainPlan.cellHeight);
  }
  context.restore();
  for (const feature of landformPlan.features) {
    context.fillStyle = feature.color;
    context.beginPath();
    context.arc(feature.x, feature.y, feature.radius, 0, Math.PI * 2);
    context.fill();
  }
  context.restore();
  return Object.freeze({
    status: "RENDERED",
    terrainDatasetId: terrainPlan.datasetId,
    terrainDatasetVersion: terrainPlan.datasetVersion,
    terrainSampleCount: terrainPlan.samples.length,
    landformDatasetId: landformPlan.datasetId,
    landformFeatureCount: landformPlan.features.length,
  });
}

export function mountPhysicalLandPresentation(documentRef, {
  terrainPublication = NOVEGEO_TERRAIN_STANDARD,
  landformPublication = NOVEGEO_LANDFORMS_STANDARD,
  boundaryPublication = BUNDLED_WORLD_BOUNDARY_PUBLICATION,
  devicePixelRatio = Number(globalThis.devicePixelRatio || 1),
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
  const terrainPlan = createTerrainRenderPlan(terrainPublication, viewport);
  const landformPlan = createLandformRenderPlan(landformPublication, viewport);
  const boundaryPlan = createBoundaryRenderPlan(boundaryPublication, viewport);

  const existingCanvas = container.querySelector?.("[data-role='novegeo-physical-land-canvas']");
  const canvas = existingCanvas || documentRef.createElement("canvas");
  canvas.setAttribute("data-role", "novegeo-physical-land-canvas");
  canvas.setAttribute("aria-hidden", "true");
  if (container.style) container.style.position = "relative";
  if (boundaryCanvas.style) Object.assign(boundaryCanvas.style, { position: "relative", zIndex: P004_MAP_Z_INDEX });
  if (!existingCanvas) {
    if (typeof container.insertBefore === "function") container.insertBefore(canvas, boundaryCanvas);
    else if (typeof container.appendChild === "function") container.appendChild(canvas);
  }

  return renderPhysicalLandCanvas({ canvas, viewport, terrainPlan, landformPlan, boundaryPlan });
}
