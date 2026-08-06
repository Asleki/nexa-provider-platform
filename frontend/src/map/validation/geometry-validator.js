/** Deep MultiPolygon validation for governed NoveGeo boundary publications. */
import { createGeographicCoordinate } from "../geography/contracts.js";

function samePosition(left, right) {
  return left[0] === right[0] && left[1] === right[1];
}

function positionKey(position) {
  return `${position[0]}:${position[1]}`;
}

export function validateBoundaryGeometry(geometry) {
  if (!geometry || geometry.type !== "MultiPolygon") {
    throw new TypeError("boundary geometry must be a MultiPolygon");
  }
  if (!Array.isArray(geometry.coordinates) || geometry.coordinates.length === 0) {
    throw new Error("boundary MultiPolygon must contain at least one polygon");
  }

  let ringCount = 0;
  let positionCount = 0;
  const positions = [];

  geometry.coordinates.forEach((polygon, polygonIndex) => {
    if (!Array.isArray(polygon) || polygon.length === 0) {
      throw new Error(`boundary polygon ${polygonIndex} must contain at least one ring`);
    }
    polygon.forEach((ring, ringIndex) => {
      ringCount += 1;
      if (!Array.isArray(ring) || ring.length < 4) {
        throw new Error(`boundary ring ${polygonIndex}:${ringIndex} must contain at least four positions`);
      }
      const normalizedRing = [];
      ring.forEach((position, positionIndex) => {
        if (!Array.isArray(position) || position.length < 2) {
          throw new TypeError(`boundary position ${polygonIndex}:${ringIndex}:${positionIndex} is invalid`);
        }
        const coordinate = createGeographicCoordinate(position[0], position[1]);
        const normalized = Object.freeze([coordinate.longitude, coordinate.latitude]);
        if (positionIndex > 0 && samePosition(normalizedRing[positionIndex - 1], normalized)) {
          throw new Error(`boundary ring ${polygonIndex}:${ringIndex} contains consecutive duplicate positions`);
        }
        normalizedRing.push(normalized);
      });
      if (!samePosition(normalizedRing[0], normalizedRing.at(-1))) {
        throw new Error(`boundary ring ${polygonIndex}:${ringIndex} must be closed`);
      }
      const distinctVertices = new Set(normalizedRing.slice(0, -1).map(positionKey));
      if (distinctVertices.size < 3) {
        throw new Error(`boundary ring ${polygonIndex}:${ringIndex} must contain at least three distinct vertices`);
      }
      positionCount += normalizedRing.length;
      positions.push(...normalizedRing);
    });
  });

  return Object.freeze({
    geometryType: geometry.type,
    polygonCount: geometry.coordinates.length,
    ringCount,
    positionCount,
    positions: Object.freeze(positions),
  });
}
