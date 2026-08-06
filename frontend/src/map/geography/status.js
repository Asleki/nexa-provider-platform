/** Minimal P004.1-P004.2 status integration; rendering is deferred to P004.3. */
import { COORDINATE_REFERENCE } from "./contracts.js";
import { PROJECTION_ID, PROJECTION_VERSION } from "./projection.js";

export function renderWorldGeometryStatus(documentRef, publication = null) {
  const boundary = documentRef.querySelector("[data-role='world-boundary-status']");
  const reference = documentRef.querySelector("[data-role='coordinate-reference-status']");
  const projection = documentRef.querySelector("[data-role='projection-status']");
  if (boundary) boundary.textContent = publication ? `Available · v${publication.boundaryVersion}` : "Bundled authority fixture ready";
  if (reference) reference.textContent = `${COORDINATE_REFERENCE.coordinateReferenceId} · v${COORDINATE_REFERENCE.version}`;
  if (projection) projection.textContent = `${PROJECTION_ID} · v${PROJECTION_VERSION}`;
  return Object.freeze({ boundaryReady: Boolean(boundary), coordinateReferenceReady: Boolean(reference), projectionReady: Boolean(projection) });
}
