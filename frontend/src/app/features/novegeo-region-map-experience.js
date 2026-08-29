/** P006.7.11.15.6.3 — additive PWA bridge from national-map API REGIONs to cartography. */
import { resolveLiveApiBaseUrl } from "../../config/live-api-endpoint.js";
import { createLiveWorldBoundaryClient } from "../../map/geography/live-boundary-client.js";
import { createNationalMapClient } from "../../map/nngla/national-map-client.js";
import { mountNoveGeoRegionCartographicOverlay } from "../../map/cartography/region-cartographic-overlay.js";
import { assertOfficialNoveGeoRegionSet } from "../../map/cartography/region-anchor.js";

function delay(windowRef, milliseconds) {
  return new Promise((resolve) => (windowRef?.setTimeout || globalThis.setTimeout)(resolve, milliseconds));
}

async function waitForMapCanvas(documentRef, windowRef, { attempts = 120, delayMs = 100 } = {}) {
  for (let index = 0; index < attempts; index += 1) {
    const page = documentRef.querySelector?.(".novegeo-feature-page");
    const viewport = page?.querySelector?.("[data-role='future-map-viewport']")
      || documentRef.querySelector?.("[data-role='future-map-viewport']");
    const canvas = viewport?.querySelector?.("[data-role='novegeo-map-canvas']");
    if (page && viewport && canvas) return { page, viewport, canvas };
    await delay(windowRef, delayMs);
  }
  throw new Error("novegeo_region_map_canvas_timeout");
}

export function installNoveGeoRegionMapExperience({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  apiBaseUrl = "",
  createBoundaryClientRef = createLiveWorldBoundaryClient,
  createMapClientRef = createNationalMapClient,
  mountOverlayRef = mountNoveGeoRegionCartographicOverlay,
} = {}) {
  let generation = 0;
  let disconnected = false;
  let overlay = null;
  let inFlight = null;

  const runRefresh = async () => {
    const page = documentRef.querySelector?.(".novegeo-feature-page");
    if (!page) return Object.freeze({ status: "INACTIVE" });
    const resolved = resolveLiveApiBaseUrl({ apiBaseUrl, windowRef });
    if (!resolved) {
      page.dataset.novegeoRegionMapStatus = "DEGRADED";
      return Object.freeze({ status: "DEGRADED", reason: "live_api_endpoint_unavailable" });
    }
    const token = ++generation;
    page.dataset.novegeoRegionMapStatus = "LOADING";
    try {
      const boundary = await createBoundaryClientRef({ apiBaseUrl: resolved, fetchRef }).getActive();
      if (disconnected || token !== generation) return Object.freeze({ status: "DISCONNECTED" });
      const extent = boundary.extent;
      const payload = await createMapClientRef({ apiBaseUrl: resolved, fetchRef }).readViewport(
        {
          minLongitude: extent.minLongitude,
          minLatitude: extent.minLatitude,
          maxLongitude: extent.maxLongitude,
          maxLatitude: extent.maxLatitude,
        },
        { families: ["ADMINISTRATIVE_AREA"], limit: 2000 }
      );
      if (disconnected || token !== generation) return Object.freeze({ status: "DISCONNECTED" });
      const regions = assertOfficialNoveGeoRegionSet(payload.items || []);
      await waitForMapCanvas(documentRef, windowRef);
      if (disconnected || token !== generation) return Object.freeze({ status: "DISCONNECTED" });
      overlay?.disconnect?.();
      overlay = mountOverlayRef(documentRef, {
        boundaryPublication: boundary,
        regionItems: regions,
        readRuntime: payload.readRuntime,
      });
      page.dataset.novegeoRegionMapStatus = overlay.status === "RENDERED" ? "READY" : overlay.status;
      page.dataset.novegeoRegionMapCount = String(regions.length);
      return Object.freeze({
        status: overlay.status,
        regionCount: regions.length,
        readRuntime: payload.readRuntime,
        semanticChecksum: payload.semanticChecksum || null,
        overlay,
      });
    } catch (error) {
      if (!disconnected && page?.dataset) page.dataset.novegeoRegionMapStatus = "DEGRADED";
      return Object.freeze({ status: "DEGRADED", reason: error?.message || String(error) });
    }
  };

  const refresh = () => {
    if (disconnected) return Promise.resolve(Object.freeze({ status: "DISCONNECTED" }));
    if (inFlight) return inFlight;
    inFlight = runRefresh().finally(() => { inFlight = null; });
    return inFlight;
  };
  const onRoute = () => queueMicrotask(() => {
    if (documentRef.querySelector?.(".novegeo-feature-page")) void refresh();
  });
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
      const page = documentRef.querySelector?.(".novegeo-feature-page");
      if (page?.dataset) {
        delete page.dataset.novegeoRegionMapStatus;
        delete page.dataset.novegeoRegionMapCount;
      }
    },
  });
}
