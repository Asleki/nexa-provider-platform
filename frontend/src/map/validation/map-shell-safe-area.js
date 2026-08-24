/** P006.7.11.15.0 / Bundle 22A — UI safe-area qualification for permanent map-shell controls. */

function finite(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

export function normalizeUiRect(rect = {}) {
  if (!rect || typeof rect !== "object") return null;
  const left = finite(rect.left ?? rect.x);
  const top = finite(rect.top ?? rect.y);
  const width = finite(rect.width);
  const height = finite(rect.height);
  const right = finite(rect.right) ?? (left !== null && width !== null ? left + width : null);
  const bottom = finite(rect.bottom) ?? (top !== null && height !== null ? top + height : null);
  if ([left, top, right, bottom].some((value) => value === null)) return null;
  if (right < left || bottom < top) return null;
  return Object.freeze({ left, top, right, bottom, width: right - left, height: bottom - top });
}

export function uiRectsIntersect(first, second) {
  const a = normalizeUiRect(first);
  const b = normalizeUiRect(second);
  if (!a || !b) return false;
  return a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top;
}

export function qualifyMapShellSafeArea({ viewportRect, permanentControlRects = [] } = {}) {
  const viewport = normalizeUiRect(viewportRect);
  if (!viewport) return Object.freeze({ status: "UNMEASURED", overlapCount: 0, overlaps: Object.freeze([]) });
  const overlaps = permanentControlRects
    .map((entry, index) => Object.freeze({ id: entry?.id || `control-${index + 1}`, rect: normalizeUiRect(entry?.rect ?? entry) }))
    .filter((entry) => entry.rect && uiRectsIntersect(viewport, entry.rect));
  return Object.freeze({
    status: overlaps.length === 0 ? "CLEAR" : "OVERLAP",
    overlapCount: overlaps.length,
    overlaps: Object.freeze(overlaps.map((entry) => entry.id)),
  });
}
