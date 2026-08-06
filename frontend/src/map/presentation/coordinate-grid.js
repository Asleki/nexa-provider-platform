/** P004.4 deterministic longitude, latitude and equator overlay generation. */
import { geographicToViewport } from "./viewport.js";
import { COORDINATE_GRID_ID, EQUATOR_OVERLAY_ID } from "./contracts.js";
import { formatLatitude, formatLongitude } from "./coordinate-labels.js";

function valuesWithin(minimum, maximum, interval) {
  const step = Number(interval);
  if (!Number.isFinite(step) || step <= 0) throw new RangeError("grid interval must be positive");
  const values = [];
  let current = Math.ceil(minimum / step) * step;
  while (current <= maximum + 1e-10) {
    values.push(Number(current.toFixed(10)));
    current += step;
  }
  return values;
}

export function createCoordinateGrid(viewport, { longitudeInterval = 5, latitudeInterval = 5 } = {}) {
  const longitudeLines = valuesWithin(viewport.extent.minLongitude, viewport.extent.maxLongitude, longitudeInterval)
    .map((longitude) => Object.freeze({
      type: "longitude",
      value: longitude,
      label: formatLongitude(longitude),
      start: geographicToViewport(longitude, viewport.extent.maxLatitude, viewport),
      end: geographicToViewport(longitude, viewport.extent.minLatitude, viewport),
    }));
  const latitudeLines = valuesWithin(viewport.extent.minLatitude, viewport.extent.maxLatitude, latitudeInterval)
    .filter((latitude) => latitude !== 0)
    .map((latitude) => Object.freeze({
      type: "latitude",
      value: latitude,
      label: formatLatitude(latitude),
      start: geographicToViewport(viewport.extent.minLongitude, latitude, viewport),
      end: geographicToViewport(viewport.extent.maxLongitude, latitude, viewport),
    }));
  const equator = viewport.extent.minLatitude <= 0 && viewport.extent.maxLatitude >= 0
    ? Object.freeze({
        overlayId: EQUATOR_OVERLAY_ID,
        type: "equator",
        value: 0,
        label: "Equator · 0°",
        start: geographicToViewport(viewport.extent.minLongitude, 0, viewport),
        end: geographicToViewport(viewport.extent.maxLongitude, 0, viewport),
      })
    : null;
  return Object.freeze({
    overlayId: COORDINATE_GRID_ID,
    overlayVersion: 1,
    longitudeInterval,
    latitudeInterval,
    longitudeLines: Object.freeze(longitudeLines),
    latitudeLines: Object.freeze(latitudeLines),
    equator,
  });
}
