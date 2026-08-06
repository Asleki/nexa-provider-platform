/** Pure viewport sizing and normalized-coordinate transformation. */
import { MAP_VIEWPORT_ID, MAP_VIEWPORT_VERSION, MapFitMode, freezeExtent } from "./contracts.js";
import { projectCoordinate } from "../geography/projection.js";

const WORLD_EXTENT = Object.freeze({ minLongitude: -180, minLatitude: -90, maxLongitude: 180, maxLatitude: 90 });

function positiveNumber(value, label) {
  const number = Number(value);
  if (!Number.isFinite(number) || number <= 0) throw new RangeError(`${label} must be a positive finite number`);
  return number;
}

export function createViewport({
  cssWidth,
  cssHeight,
  devicePixelRatio = 1,
  padding = 24,
  fitMode = MapFitMode.BOUNDARY,
  extent,
} = {}) {
  const width = positiveNumber(cssWidth, "cssWidth");
  const height = positiveNumber(cssHeight, "cssHeight");
  const ratio = Math.min(4, positiveNumber(devicePixelRatio, "devicePixelRatio"));
  const inset = Math.max(0, Number(padding));
  if (!Number.isFinite(inset) || inset * 2 >= width || inset * 2 >= height) {
    throw new RangeError("padding must leave a positive drawable viewport");
  }
  if (!Object.values(MapFitMode).includes(fitMode)) throw new Error(`unsupported map fit mode: ${fitMode}`);
  const selectedExtent = fitMode === MapFitMode.WORLD ? WORLD_EXTENT : freezeExtent(extent);
  return Object.freeze({
    viewportId: MAP_VIEWPORT_ID,
    viewportVersion: MAP_VIEWPORT_VERSION,
    cssWidth: width,
    cssHeight: height,
    devicePixelRatio: ratio,
    renderWidth: Math.round(width * ratio),
    renderHeight: Math.round(height * ratio),
    padding: inset,
    drawableWidth: width - inset * 2,
    drawableHeight: height - inset * 2,
    fitMode,
    extent: selectedExtent,
  });
}

export function geographicToViewport(longitude, latitude, viewport) {
  if (!viewport || viewport.viewportId !== MAP_VIEWPORT_ID || viewport.viewportVersion !== MAP_VIEWPORT_VERSION) {
    throw new Error("viewport uses an incompatible presentation contract");
  }
  const projected = projectCoordinate(longitude, latitude);
  const minimum = projectCoordinate(viewport.extent.minLongitude, viewport.extent.maxLatitude);
  const maximum = projectCoordinate(viewport.extent.maxLongitude, viewport.extent.minLatitude);
  const spanX = maximum.x - minimum.x;
  const spanY = maximum.y - minimum.y;
  if (spanX <= 0 || spanY <= 0) throw new RangeError("viewport extent produces an invalid projected span");
  return Object.freeze({
    x: viewport.padding + ((projected.x - minimum.x) / spanX) * viewport.drawableWidth,
    y: viewport.padding + ((projected.y - minimum.y) / spanY) * viewport.drawableHeight,
    viewportId: viewport.viewportId,
    viewportVersion: viewport.viewportVersion,
  });
}
