/** P006.2 approximate geographic scale derived from current governed view state. */
const KM_PER_DEGREE = 111.32;
const NICE_DISTANCES = Object.freeze([10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000]);

export function createScaleModel({ extent, zoom, viewportWidth }) {
  const spanDegrees = (Number(extent.maxLongitude) - Number(extent.minLongitude)) / Number(zoom);
  if (!Number.isFinite(spanDegrees) || spanDegrees <= 0) throw new RangeError("visible longitude span must be positive");
  const visibleKm = spanDegrees * KM_PER_DEGREE;
  const targetKm = visibleKm * 0.22;
  const distanceKm = [...NICE_DISTANCES].reverse().find((value) => value <= targetKm) || NICE_DISTANCES[0];
  const widthPx = Math.max(24, Math.min(Number(viewportWidth) * 0.4, (distanceKm / visibleKm) * Number(viewportWidth)));
  return Object.freeze({
    scaleModelId: "scale:novegeo:approximate-horizontal",
    distanceKm,
    widthPx,
    visibleLongitudeDegrees: spanDegrees,
    approximation: "geographic_equatorial_reference",
  });
}
