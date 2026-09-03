/** P006.7.11.15.10 — uniform contain-fit projection for the map-first viewport. */
import { projectCoordinate, unprojectCoordinate, PROJECTION_ID, PROJECTION_VERSION } from "../geography/projection.js";

export const UNIFIED_VIEWPORT_ID = "viewport:novegeo:map-first-unified";
export const UNIFIED_VIEWPORT_VERSION = 1;
const EQUIRECTANGULAR_WORLD_ASPECT_X = 2;

function positive(value, name) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) throw new RangeError(`${name} must be a positive finite number`);
  return number;
}

function finite(value, name) {
  const number = Number(value);
  if (!Number.isFinite(number)) throw new TypeError(`${name} must be finite`);
  return number;
}

function normalizeExtent(extent) {
  const value = Object.freeze({
    minLongitude: finite(extent?.minLongitude, "minLongitude"),
    minLatitude: finite(extent?.minLatitude, "minLatitude"),
    maxLongitude: finite(extent?.maxLongitude, "maxLongitude"),
    maxLatitude: finite(extent?.maxLatitude, "maxLatitude"),
  });
  if (value.minLongitude >= value.maxLongitude || value.minLatitude >= value.maxLatitude) {
    throw new RangeError("extent minimums must be lower than maximums");
  }
  return value;
}

export function createUniformProjectedViewport({
  cssWidth,
  cssHeight,
  devicePixelRatio = 1,
  padding = 24,
  extent,
} = {}) {
  const width = positive(cssWidth, "cssWidth");
  const height = positive(cssHeight, "cssHeight");
  const ratio = Math.min(4, positive(devicePixelRatio, "devicePixelRatio"));
  const inset = Math.max(0, finite(padding, "padding"));
  if (inset * 2 >= width || inset * 2 >= height) throw new RangeError("padding must leave positive drawable space");
  const normalizedExtent = normalizeExtent(extent);

  const upperLeftRaw = projectCoordinate(normalizedExtent.minLongitude, normalizedExtent.maxLatitude);
  const lowerRightRaw = projectCoordinate(normalizedExtent.maxLongitude, normalizedExtent.minLatitude);
  // The locked projection normalizes longitude over 360° and latitude over 180°.
  // Convert normalized X into the same angular scale as Y before contain-fit so
  // one projected degree is never stretched differently by viewport shape.
  const upperLeft = { x: upperLeftRaw.x * EQUIRECTANGULAR_WORLD_ASPECT_X, y: upperLeftRaw.y };
  const lowerRight = { x: lowerRightRaw.x * EQUIRECTANGULAR_WORLD_ASPECT_X, y: lowerRightRaw.y };
  const projectedSpanX = lowerRight.x - upperLeft.x;
  const projectedSpanY = lowerRight.y - upperLeft.y;
  if (!(projectedSpanX > 0 && projectedSpanY > 0)) throw new RangeError("extent produces an invalid projected span");

  const drawableWidth = width - inset * 2;
  const drawableHeight = height - inset * 2;
  const widthScale = drawableWidth / projectedSpanX;
  const heightScale = drawableHeight / projectedSpanY;
  const uniformScale = Math.min(widthScale, heightScale);
  const fittedWidth = projectedSpanX * uniformScale;
  const fittedHeight = projectedSpanY * uniformScale;
  const originX = (width - fittedWidth) / 2;
  const originY = (height - fittedHeight) / 2;

  return Object.freeze({
    viewportId: UNIFIED_VIEWPORT_ID,
    viewportVersion: UNIFIED_VIEWPORT_VERSION,
    projectionId: PROJECTION_ID,
    projectionVersion: PROJECTION_VERSION,
    cssWidth: width,
    cssHeight: height,
    renderWidth: Math.round(width * ratio),
    renderHeight: Math.round(height * ratio),
    devicePixelRatio: ratio,
    padding: inset,
    extent: normalizedExtent,
    projectedMinimumX: upperLeft.x,
    projectedMinimumY: upperLeft.y,
    projectedSpanX,
    projectedSpanY,
    widthScale,
    heightScale,
    uniformScale,
    fittedWidth,
    fittedHeight,
    originX,
    originY,
  });
}

function assertViewport(viewport) {
  if (!viewport || viewport.viewportId !== UNIFIED_VIEWPORT_ID || viewport.viewportVersion !== UNIFIED_VIEWPORT_VERSION) {
    throw new Error("viewport uses an incompatible unified presentation contract");
  }
}

export function geographicToUnifiedViewport(longitude, latitude, viewport) {
  assertViewport(viewport);
  const raw = projectCoordinate(longitude, latitude);
  const projected = { x: raw.x * EQUIRECTANGULAR_WORLD_ASPECT_X, y: raw.y };
  return Object.freeze({
    x: viewport.originX + (projected.x - viewport.projectedMinimumX) * viewport.uniformScale,
    y: viewport.originY + (projected.y - viewport.projectedMinimumY) * viewport.uniformScale,
  });
}

export function applyNavigationToPoint(point, viewport, navigation = {}) {
  assertViewport(viewport);
  const zoom = positive(navigation.zoom ?? 1, "navigation.zoom");
  const offsetX = finite(navigation.offsetX ?? 0, "navigation.offsetX");
  const offsetY = finite(navigation.offsetY ?? 0, "navigation.offsetY");
  const centerX = viewport.cssWidth / 2;
  const centerY = viewport.cssHeight / 2;
  return Object.freeze({
    x: centerX + (Number(point.x) - centerX) * zoom + offsetX,
    y: centerY + (Number(point.y) - centerY) * zoom + offsetY,
  });
}

export function geographicToNavigatedViewport(longitude, latitude, viewport, navigation = {}) {
  return applyNavigationToPoint(geographicToUnifiedViewport(longitude, latitude, viewport), viewport, navigation);
}

export function viewportPointToGeographic(x, y, viewport, navigation = {}) {
  assertViewport(viewport);
  const zoom = positive(navigation.zoom ?? 1, "navigation.zoom");
  const offsetX = finite(navigation.offsetX ?? 0, "navigation.offsetX");
  const offsetY = finite(navigation.offsetY ?? 0, "navigation.offsetY");
  const centerX = viewport.cssWidth / 2;
  const centerY = viewport.cssHeight / 2;
  const baseX = (finite(x, "x") - offsetX - centerX) / zoom + centerX;
  const baseY = (finite(y, "y") - offsetY - centerY) / zoom + centerY;
  const projectedX = viewport.projectedMinimumX + (baseX - viewport.originX) / viewport.uniformScale;
  const projectedY = viewport.projectedMinimumY + (baseY - viewport.originY) / viewport.uniformScale;
  return unprojectCoordinate(Object.freeze({
    x: projectedX / EQUIRECTANGULAR_WORLD_ASPECT_X,
    y: projectedY,
    projectionId: PROJECTION_ID,
    projectionVersion: PROJECTION_VERSION,
  }));
}
