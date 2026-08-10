/**
 * Bundle 12E Omega — NoveGeo feature geometry normalization.
 *
 * Keeps the feature-page presentation additive above locked P004-P006 map contracts:
 * - the visible feature viewport is the actual interactive drawable surface;
 * - compact-screen opening magnification is expressed through the P006 controller;
 * - saved runtime-scoped view state always wins over the default opening view;
 * - resize/orientation changes redraw every presentation layer against one viewport width,
 *   then reconstrain the existing P006 navigation state without changing its semantics.
 */

export const NOVEGEO_COMPACT_BREAKPOINT_PX = 704;
export const NOVEGEO_COMPACT_OPENING_ZOOM = 1.25;
export const NOVEGEO_WIDE_OPENING_ZOOM = 1;

function finiteWidth(value) {
  const width = Number(value);
  return Number.isFinite(width) && width > 0 ? width : 0;
}

export function measureNoveGeoDrawableWidth(viewport) {
  const rect = viewport?.getBoundingClientRect?.();
  return finiteWidth(rect?.width) || finiteWidth(viewport?.clientWidth) || 0;
}

export function defaultNoveGeoOpeningZoom({ viewportWidth } = {}) {
  const width = finiteWidth(viewportWidth);
  if (!width) return NOVEGEO_WIDE_OPENING_ZOOM;
  return width <= NOVEGEO_COMPACT_BREAKPOINT_PX
    ? NOVEGEO_COMPACT_OPENING_ZOOM
    : NOVEGEO_WIDE_OPENING_ZOOM;
}

export function hasRestoredNoveGeoView(stateIntegration) {
  return stateIntegration?.viewState?.latestReceipt?.status === "RESTORED";
}

export function applyDefaultNoveGeoOpeningView({ viewport, discovery, stateIntegration } = {}) {
  const controller = discovery?.controller;
  if (!viewport || !controller) return Object.freeze({ status: "UNAVAILABLE", reason: "navigation_unavailable" });
  if (hasRestoredNoveGeoView(stateIntegration)) {
    return Object.freeze({ status: "PRESERVED", reason: "restored_view_state", zoom: controller.state.zoom });
  }

  const targetZoom = defaultNoveGeoOpeningZoom({ viewportWidth: measureNoveGeoDrawableWidth(viewport) });
  if (Math.abs(Number(controller.state.zoom) - targetZoom) < 0.0005) {
    return Object.freeze({ status: "READY", reused: true, zoom: controller.state.zoom });
  }

  controller.zoomTo?.(targetZoom, "feature-opening-view");
  return Object.freeze({ status: "READY", reused: false, zoom: controller.state.zoom });
}

export function createNoveGeoResizeCoordinator({
  viewport,
  windowRef = globalThis.window,
  discovery,
  redraw,
} = {}) {
  const controller = discovery?.controller;
  if (!viewport || !controller || typeof redraw !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "resize_dependencies_missing", disconnect() {} });
  }

  let disposed = false;
  let queued = false;
  let lastWidth = measureNoveGeoDrawableWidth(viewport);

  const reconcile = () => {
    if (disposed) return Object.freeze({ status: "DISPOSED" });
    const width = measureNoveGeoDrawableWidth(viewport);
    if (width && lastWidth && Math.abs(width - lastWidth) < 1) {
      return Object.freeze({ status: "UNCHANGED", width });
    }
    if (width) lastWidth = width;
    const renderReceipt = redraw();
    controller.zoomTo?.(controller.state.zoom, "feature-viewport-resize");
    return Object.freeze({ status: "READY", width, renderReceipt });
  };

  const schedule = () => {
    if (disposed || queued) return;
    queued = true;
    const run = () => {
      queued = false;
      reconcile();
    };
    if (typeof windowRef?.requestAnimationFrame === "function") windowRef.requestAnimationFrame(run);
    else queueMicrotask(run);
  };

  const ResizeObserverCtor = windowRef?.ResizeObserver ?? globalThis.ResizeObserver;
  let observer = null;
  if (typeof ResizeObserverCtor === "function") {
    observer = new ResizeObserverCtor(schedule);
    observer.observe(viewport);
  }

  const onOrientation = () => schedule();
  windowRef?.addEventListener?.("orientationchange", onOrientation);

  return Object.freeze({
    status: "READY",
    reconcile,
    schedule,
    disconnect() {
      if (disposed) return;
      disposed = true;
      observer?.disconnect?.();
      windowRef?.removeEventListener?.("orientationchange", onOrientation);
    },
  });
}
