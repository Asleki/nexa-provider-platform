/** P006.7.11.15.4 — additive cartographic styling/label experience for the NoveGeo map route. */
import { resolveLiveApiBaseUrl } from "../../config/live-api-endpoint.js";
import { createLiveWorldBoundaryClient } from "../../map/geography/live-boundary-client.js";
import { mountNoveGeoCartographicOverlay } from "../../map/cartography/cartographic-overlay.js";

export const NOVEGEO_CARTOGRAPHY_STYLE_HREF = "./styles/novegeo-cartography-v1.css";

function ensureStylesheet(documentRef) {
  const existing = documentRef.querySelector?.("link[data-novegeo-cartography-style='true']");
  if (existing) return existing;
  if (!documentRef?.createElement || !documentRef?.head?.appendChild) return null;
  const link = documentRef.createElement("link");
  link.rel = "stylesheet";
  link.href = NOVEGEO_CARTOGRAPHY_STYLE_HREF;
  link.dataset.novegeoCartographyStyle = "true";
  documentRef.head.appendChild(link);
  return link;
}

function delay(windowRef, milliseconds) {
  return new Promise((resolve) => (windowRef?.setTimeout || globalThis.setTimeout)(resolve, milliseconds));
}

async function waitForMapCanvas(documentRef, windowRef, { attempts = 120, delayMs = 100 } = {}) {
  for (let index = 0; index < attempts; index += 1) {
    const page = documentRef.querySelector?.(".novegeo-feature-page");
    const viewport = page?.querySelector?.("[data-role='future-map-viewport']") || documentRef.querySelector?.("[data-role='future-map-viewport']");
    const canvas = viewport?.querySelector?.("[data-role='novegeo-map-canvas']");
    if (page && viewport && canvas) return { page, viewport, canvas };
    await delay(windowRef, delayMs);
  }
  throw new Error("novegeo_map_canvas_timeout");
}

export function installNoveGeoCartographicStylingExperience({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  apiBaseUrl = "",
  createBoundaryClientRef = createLiveWorldBoundaryClient,
  mountOverlayRef = mountNoveGeoCartographicOverlay,
} = {}) {
  ensureStylesheet(documentRef);
  let generation = 0;
  let disconnected = false;
  let overlay = null;
  let inFlight = null;

  const runRefresh = async () => {
    const page = documentRef.querySelector?.(".novegeo-feature-page");
    if (!page) return Object.freeze({ status: "INACTIVE" });
    const resolved = resolveLiveApiBaseUrl({ apiBaseUrl, windowRef });
    if (!resolved) return Object.freeze({ status: "DEGRADED", reason: "live_api_endpoint_unavailable" });
    const token = ++generation;
    try {
      const boundary = await createBoundaryClientRef({ apiBaseUrl: resolved, fetchRef }).getActive();
      if (disconnected || token !== generation) return Object.freeze({ status: "DISCONNECTED" });
      await waitForMapCanvas(documentRef, windowRef);
      if (disconnected || token !== generation) return Object.freeze({ status: "DISCONNECTED" });
      overlay?.disconnect?.();
      overlay = mountOverlayRef(documentRef, { boundaryPublication: boundary });
      page.dataset.cartographicStyling = overlay.status === "RENDERED" ? "READY" : overlay.status;
      return Object.freeze({ status: overlay.status, boundaryVersion: boundary.boundaryVersion, overlay });
    } catch (error) {
      if (!disconnected && page?.dataset) page.dataset.cartographicStyling = "DEGRADED";
      return Object.freeze({ status: "DEGRADED", reason: error?.message || String(error) });
    }
  };

  const refresh = () => {
    if (disconnected) return Promise.resolve(Object.freeze({ status: "DISCONNECTED" }));
    if (inFlight) return inFlight;
    inFlight = runRefresh().finally(() => { inFlight = null; });
    return inFlight;
  };
  const onRoute = () => queueMicrotask(() => { if (documentRef.querySelector?.(".novegeo-feature-page")) void refresh(); });
  windowRef?.addEventListener?.("hashchange", onRoute);
  onRoute();

  return Object.freeze({
    status: "READY",
    refresh,
    get overlay() { return overlay; },
    disconnect() {
      disconnected = true;
      generation += 1;
      windowRef?.removeEventListener?.("hashchange", onRoute);
      overlay?.disconnect?.();
      overlay = null;
    },
  });
}
