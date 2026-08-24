/** P006.7.11.15.4 — zoom-aware deterministic cartographic label planning. */
import { resolveCartographicStyle, renderCartographicText } from "./style-catalog.js";

function candidateKey(candidate) {
  return candidate.labelGroupReference || `${candidate.labelClass}:${candidate.subjectId}`;
}

export function createCartographicLabelPlan({ candidates = [], zoom = 1, project } = {}) {
  if (typeof project !== "function") throw new TypeError("project must be a function");
  const selected = new Map();
  for (const candidate of candidates) {
    if (!candidate || typeof candidate !== "object") throw new TypeError("cartographic candidate must be an object");
    const style = resolveCartographicStyle(candidate.labelClass, zoom);
    if (!style.eligible) continue;
    const key = candidateKey(candidate);
    const previous = selected.get(key);
    if (!previous || style.priority > previous.style.priority || (style.priority === previous.style.priority && candidate.subjectId < previous.candidate.subjectId)) {
      selected.set(key, { candidate, style });
    }
  }
  const labels = [...selected.values()].map(({ candidate, style }) => {
    const point = project(candidate.anchor.longitude, candidate.anchor.latitude);
    if (!point || !Number.isFinite(Number(point.x)) || !Number.isFinite(Number(point.y))) throw new Error("project returned an invalid viewport point");
    return Object.freeze({
      subjectId: candidate.subjectId,
      labelGroupReference: candidate.labelGroupReference,
      labelClass: candidate.labelClass,
      displayName: candidate.displayName,
      renderedText: renderCartographicText(candidate.displayName, style),
      publicationReference: candidate.publicationReference,
      runtimeMode: candidate.runtimeMode,
      anchor: candidate.anchor,
      x: Number(point.x),
      y: Number(point.y),
      style,
      priority: style.priority,
    });
  }).sort((a, b) => b.priority - a.priority || a.labelClass.localeCompare(b.labelClass) || a.subjectId.localeCompare(b.subjectId));
  return Object.freeze({
    planId: "render-plan:novegeo:cartographic-labels",
    planVersion: 1,
    zoom: Number(zoom),
    labels: Object.freeze(labels),
  });
}
