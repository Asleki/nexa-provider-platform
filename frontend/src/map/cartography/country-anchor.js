/** P006.7.11.15.4 — deterministic presentation-only country label anchor. */
import { validateWorldBoundaryPublication } from "../geography/contracts.js";
import { CartographicAnchorKind, CartographicLabelClass, createCartographicLabelCandidate, createPresentationAnchor } from "./contracts.js";

export const COUNTRY_LABEL_ANCHOR_ALGORITHM_ID = "cartography:novegeo:country-mainland-interior";
export const COUNTRY_LABEL_ANCHOR_ALGORITHM_VERSION = 1;

function ringArea(ring) {
  let twiceArea = 0;
  for (let i = 0; i < ring.length - 1; i += 1) {
    const [x1, y1] = ring[i];
    const [x2, y2] = ring[i + 1];
    twiceArea += x1 * y2 - x2 * y1;
  }
  return twiceArea / 2;
}

function pointInRing([x, y], ring) {
  let inside = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i, i += 1) {
    const [xi, yi] = ring[i];
    const [xj, yj] = ring[j];
    const intersects = ((yi > y) !== (yj > y)) && (x < ((xj - xi) * (y - yi)) / ((yj - yi) || Number.EPSILON) + xi);
    if (intersects) inside = !inside;
  }
  return inside;
}

function pointInPolygon(point, polygon) {
  if (!pointInRing(point, polygon[0])) return false;
  return polygon.slice(1).every((hole) => !pointInRing(point, hole));
}

function segmentDistanceSquared([px, py], [ax, ay], [bx, by]) {
  const dx = bx - ax;
  const dy = by - ay;
  if (dx === 0 && dy === 0) return (px - ax) ** 2 + (py - ay) ** 2;
  const t = Math.max(0, Math.min(1, ((px - ax) * dx + (py - ay) * dy) / (dx * dx + dy * dy)));
  const qx = ax + t * dx;
  const qy = ay + t * dy;
  return (px - qx) ** 2 + (py - qy) ** 2;
}

function distanceToPolygonEdges(point, polygon) {
  let best = Infinity;
  for (const ring of polygon) {
    for (let i = 0; i < ring.length - 1; i += 1) {
      best = Math.min(best, segmentDistanceSquared(point, ring[i], ring[i + 1]));
    }
  }
  return Math.sqrt(best);
}

function boundsOf(ring) {
  const xs = ring.map((position) => Number(position[0]));
  const ys = ring.map((position) => Number(position[1]));
  return { minX: Math.min(...xs), maxX: Math.max(...xs), minY: Math.min(...ys), maxY: Math.max(...ys) };
}

function stableInteriorPoint(polygon) {
  const exterior = polygon[0];
  const bounds = boundsOf(exterior);
  const spanX = bounds.maxX - bounds.minX;
  const spanY = bounds.maxY - bounds.minY;
  if (!(spanX > 0 && spanY > 0)) throw new Error("country mainland polygon has no drawable area");

  let best = null;
  const consider = (x, y) => {
    const point = [x, y];
    if (!pointInPolygon(point, polygon)) return;
    const score = distanceToPolygonEdges(point, polygon);
    if (!best || score > best.score + 1e-12 || (Math.abs(score - best.score) <= 1e-12 && (y > best.y || (y === best.y && x < best.x)))) {
      best = { x, y, score };
    }
  };

  const GRID = 24;
  for (let ix = 0; ix <= GRID; ix += 1) {
    for (let iy = 0; iy <= GRID; iy += 1) {
      consider(bounds.minX + (spanX * ix) / GRID, bounds.minY + (spanY * iy) / GRID);
    }
  }
  if (!best) throw new Error("no interior country label anchor could be derived");

  let stepX = spanX / GRID;
  let stepY = spanY / GRID;
  for (let pass = 0; pass < 4; pass += 1) {
    const center = best;
    for (const dx of [-1, -0.5, 0, 0.5, 1]) {
      for (const dy of [-1, -0.5, 0, 0.5, 1]) consider(center.x + dx * stepX, center.y + dy * stepY);
    }
    stepX /= 2;
    stepY /= 2;
  }
  return Object.freeze({ longitude: best.x, latitude: best.y });
}

export function deriveCountryLabelAnchor(boundaryPublication) {
  const publication = validateWorldBoundaryPublication(boundaryPublication);
  const polygons = publication.geometry.coordinates;
  if (!Array.isArray(polygons) || polygons.length === 0) throw new Error("country boundary has no polygons");
  const mainland = [...polygons].sort((a, b) => Math.abs(ringArea(b[0])) - Math.abs(ringArea(a[0])))[0];
  const point = stableInteriorPoint(mainland);
  return createPresentationAnchor({
    kind: CartographicAnchorKind.DERIVED_PRESENTATION,
    longitude: point.longitude,
    latitude: point.latitude,
    sourceBoundaryId: publication.boundaryId,
    sourceBoundaryVersion: publication.boundaryVersion,
    algorithmId: COUNTRY_LABEL_ANCHOR_ALGORITHM_ID,
    algorithmVersion: COUNTRY_LABEL_ANCHOR_ALGORITHM_VERSION,
  });
}

export function createNoveGeoCountryLabelCandidate(boundaryPublication, {
  countryId = "country:novegeo",
  displayName = "NoveGeo",
} = {}) {
  const publication = validateWorldBoundaryPublication(boundaryPublication);
  return createCartographicLabelCandidate({
    subjectId: countryId,
    displayName,
    labelClass: CartographicLabelClass.COUNTRY,
    anchor: deriveCountryLabelAnchor(publication),
    runtimeMode: "shared_reference",
    publicationReference: publication.publicationId || null,
    labelGroupReference: countryId,
  });
}
