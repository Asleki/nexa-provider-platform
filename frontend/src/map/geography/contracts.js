/** P004.1-P004.2 immutable browser geography contracts. */

export const COORDINATE_REFERENCE = Object.freeze({
  coordinateReferenceId: "crs:novegeo:geographic",
  version: 1,
  authorityName: "EPSG",
  authorityCode: "4326",
  axisOrder: Object.freeze(["longitude", "latitude"]),
  unit: "decimal_degrees",
});

export function createGeographicCoordinate(longitude, latitude) {
  const lon = Number(longitude);
  const lat = Number(latitude);
  if (!Number.isFinite(lon) || !Number.isFinite(lat)) throw new TypeError("coordinates must be finite");
  if (lon < -180 || lon > 180) throw new RangeError("longitude must be between -180 and 180");
  if (lat < -90 || lat > 90) throw new RangeError("latitude must be between -90 and 90");
  return Object.freeze({ longitude: lon, latitude: lat });
}

export function validateWorldBoundaryPublication(value) {
  if (!value || typeof value !== "object") throw new TypeError("world boundary publication must be an object");
  if (!String(value.boundaryId || "").startsWith("boundary:")) throw new Error("boundaryId is invalid");
  if (!Number.isInteger(value.boundaryVersion) || value.boundaryVersion < 1) throw new Error("boundaryVersion is invalid");
  if (value.geometry?.type !== "MultiPolygon") throw new Error("published boundary must use MultiPolygon");
  const reference = value.coordinateReference;
  if (reference?.coordinateReferenceId !== COORDINATE_REFERENCE.coordinateReferenceId || reference?.version !== 1) {
    throw new Error("unsupported coordinate reference");
  }
  if (JSON.stringify(reference.axisOrder) !== JSON.stringify(COORDINATE_REFERENCE.axisOrder)) {
    throw new Error("coordinate axis order is incompatible");
  }
  return Object.freeze(value);
}
