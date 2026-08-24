/** P006.7.11.15.4 — deterministic screen-space label collision/decluttering. */

function overlaps(a, b) {
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

export function labelCollisionBox(label, metrics) {
  const width = Number(metrics?.width);
  const height = Number(metrics?.height);
  if (!(Number.isFinite(width) && width >= 0 && Number.isFinite(height) && height > 0)) throw new RangeError("label metrics must contain finite positive dimensions");
  const padding = Number(label?.style?.collisionPaddingPx || 0);
  const halfWidth = width / 2 + padding;
  const halfHeight = height / 2 + padding;
  return Object.freeze({
    left: label.x - halfWidth,
    right: label.x + halfWidth,
    top: label.y - halfHeight,
    bottom: label.y + halfHeight,
  });
}

export function declutterCartographicLabels(measuredLabels = []) {
  const accepted = [];
  const rejected = [];
  const ordered = [...measuredLabels].sort((a, b) => b.label.priority - a.label.priority || a.label.subjectId.localeCompare(b.label.subjectId));
  for (const item of ordered) {
    const box = labelCollisionBox(item.label, item.metrics);
    if (accepted.some((existing) => overlaps(existing.box, box))) rejected.push(Object.freeze({ ...item, box, reason: "collision" }));
    else accepted.push(Object.freeze({ ...item, box }));
  }
  return Object.freeze({
    accepted: Object.freeze(accepted),
    rejected: Object.freeze(rejected),
  });
}
