/** P006.7.11.15.10 — centre-sampled geodesic distance scale. */
import { viewportPointToGeographic } from "./unified-projection.js";

export const GEODESIC_SCALE_ID = "scale:novegeo:map-first-centre-sampled";
export const GEODESIC_SCALE_VERSION = 1;

const EARTH_RADIUS_KM = 6371.0088;
const MILES_PER_KM = 0.621371192237334;
const NICE_KM = Object.freeze([
  0.1, 0.2, 0.5,
  1, 2, 5,
  10, 20, 50,
  100, 200, 500,
  1000, 2000, 5000,
]);

function radians(degrees) { return Number(degrees) * Math.PI / 180; }

export function geodesicDistanceKm(a, b) {
  const lat1 = radians(a?.latitude);
  const lat2 = radians(b?.latitude);
  const dLat = lat2 - lat1;
  const dLon = radians(Number(b?.longitude) - Number(a?.longitude));
  if (![lat1, lat2, dLat, dLon].every(Number.isFinite)) throw new TypeError("geodesic coordinates must be finite");
  const h = Math.sin(dLat / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(dLon / 2) ** 2;
  return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(Math.max(0, 1 - h)));
}

function chooseNiceDistance(targetKm) {
  const target = Number(targetKm);
  if (!Number.isFinite(target) || target <= 0) throw new RangeError("target distance must be positive");
  return [...NICE_KM].reverse().find((value) => value <= target) || NICE_KM[0];
}

function formatMiles(kilometres) {
  const miles = kilometres * MILES_PER_KM;
  if (miles < 10) return Number(miles.toFixed(1));
  return Math.round(miles);
}

export function createGeodesicScaleModel({ viewport, navigation, targetWidthPx = 112 } = {}) {
  const requestedWidth = Math.max(48, Math.min(180, Number(targetWidthPx) || 112));
  const y = viewport.cssHeight / 2;
  const centreX = viewport.cssWidth / 2;
  const half = requestedWidth / 2;
  const left = viewportPointToGeographic(centreX - half, y, viewport, navigation);
  const right = viewportPointToGeographic(centreX + half, y, viewport, navigation);
  const sampledDistanceKm = geodesicDistanceKm(left, right);
  const distanceKm = chooseNiceDistance(sampledDistanceKm);
  const widthPx = Math.max(24, requestedWidth * (distanceKm / sampledDistanceKm));
  const distanceMiles = formatMiles(distanceKm);
  return Object.freeze({
    scaleModelId: GEODESIC_SCALE_ID,
    scaleModelVersion: GEODESIC_SCALE_VERSION,
    sampleLatitude: Number(((left.latitude + right.latitude) / 2).toFixed(6)),
    sampledDistanceKm,
    distanceKm,
    distanceMiles,
    widthPx: Number(widthPx.toFixed(3)),
    metricLabel: `${distanceKm} km`,
    imperialLabel: `${distanceMiles} mi`,
    approximation: "screen_sampled_geodesic_at_viewport_centre",
  });
}
