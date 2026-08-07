/**
 * Bundle 11.0B — additive mobile/browser foreground recovery for map pixels.
 * Reuses existing governed P004/P005 renderers after tab/app suspension.
 */

function scheduleOnce(callback, scheduler = globalThis.requestAnimationFrame) {
  let scheduled = false;

  return () => {
    if (scheduled) return false;
    scheduled = true;

    const run = () => {
      scheduled = false;
      callback();
    };

    if (typeof scheduler === "function") scheduler(run);
    else run();
    return true;
  };
}

export function registerMapForegroundRecovery({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  redrawMap,
  redrawPhysicalLand,
  scheduler = globalThis.requestAnimationFrame,
} = {}) {
  if (!documentRef || typeof documentRef.addEventListener !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "document_events_unavailable" });
  }
  if (typeof redrawMap !== "function" || typeof redrawPhysicalLand !== "function") {
    throw new TypeError("redrawMap and redrawPhysicalLand must be functions");
  }

  let repaintCount = 0;
  let lastReceipt = null;

  const repaint = scheduleOnce(() => {
    const map = redrawMap();
    const physicalLand = redrawPhysicalLand();
    repaintCount += 1;
    lastReceipt = Object.freeze({
      status: "REPAINTED",
      repaintCount,
      mapStatus: map?.status ?? "UNKNOWN",
      physicalLandStatus: physicalLand?.status ?? "UNKNOWN",
    });
  }, scheduler);

  const onVisibilityChange = () => {
    if (documentRef.visibilityState === "visible" || documentRef.hidden === false) repaint();
  };

  const onPageShow = () => repaint();

  documentRef.addEventListener("visibilitychange", onVisibilityChange);
  if (windowRef && typeof windowRef.addEventListener === "function") {
    windowRef.addEventListener("pageshow", onPageShow);
  }

  return Object.freeze({
    status: "REGISTERED",
    repaint,
    get repaintCount() { return repaintCount; },
    get latestReceipt() { return lastReceipt; },
    disconnect() {
      documentRef.removeEventListener?.("visibilitychange", onVisibilityChange);
      windowRef?.removeEventListener?.("pageshow", onPageShow);
    },
  });
}
