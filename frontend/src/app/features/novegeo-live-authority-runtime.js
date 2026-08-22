/** P006.7.11.9 — Live NoveGeo composition: API authority first, rendering second. */
import { resolveLiveApiBaseUrl } from "../../config/live-api-endpoint.js";
import { createLiveWorldBoundaryClient } from "../../map/geography/live-boundary-client.js";
import { mountLiveNnglaPublicationStatus } from "../../map/nngla/live-publication-status.js";
import { mountNoveGeoFeatureRuntime } from "./novegeo-feature-runtime.js";

function setAuthorityState(viewport, statusNode, visibleStatusNode, { status, source = "api-postgresql", message, boundaryVersion = null } = {}) {
  if (viewport?.dataset) {
    viewport.dataset.authorityStatus = status;
    viewport.dataset.authoritySource = source;
    if (boundaryVersion === null) delete viewport.dataset.authorityBoundaryVersion;
    else viewport.dataset.authorityBoundaryVersion = String(boundaryVersion);
  }
  if (statusNode) statusNode.textContent = message;
  if (visibleStatusNode) {
    visibleStatusNode.textContent = message;
    if (visibleStatusNode.dataset) visibleStatusNode.dataset.status = status;
  }
}

export function mountNoveGeoLiveAuthorityRuntime({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  apiBaseUrl = "",
  runtimeMode = "simulation",
  createBoundaryClientRef = createLiveWorldBoundaryClient,
  mountFeatureRef = mountNoveGeoFeatureRuntime,
} = {}) {
  const viewport = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  if (!viewport) return Object.freeze({ status: "UNAVAILABLE", reason: "feature_viewport_missing", disconnect() {} });
  const statusNode = documentRef?.querySelector?.("[data-role='map-render-status']");
  const visibleStatusNode = documentRef?.querySelector?.("[data-role='novegeo-authority-state']");
  const resolvedApiBaseUrl = resolveLiveApiBaseUrl({ apiBaseUrl, windowRef });
  let disconnected = false;
  let featureRuntime = null;

  if (!resolvedApiBaseUrl) {
    setAuthorityState(viewport, statusNode, visibleStatusNode, {
      status: "DEGRADED",
      message: "Live NoveGeo authority unavailable. No bundled sovereign boundary has been substituted.",
    });
    return Object.freeze({
      status: "DEGRADED",
      reason: "live_api_endpoint_unavailable",
      apiBaseUrl: "",
      ready: Promise.resolve(Object.freeze({ status: "DEGRADED", reason: "live_api_endpoint_unavailable" })),
      disconnect() { disconnected = true; },
    });
  }

  setAuthorityState(viewport, statusNode, visibleStatusNode, {
    status: "LOADING",
    message: "Loading authoritative NoveGeo boundary from the live API…",
  });

  const client = createBoundaryClientRef({ apiBaseUrl: resolvedApiBaseUrl, fetchRef });
  const ready = client.getActive().then((boundaryPublication) => {
    if (disconnected) return Object.freeze({ status: "DISCONNECTED" });
    featureRuntime = mountFeatureRef({
      documentRef,
      windowRef,
      runtimeMode,
      boundaryPublication,
      nnglaPublicationMount: mountLiveNnglaPublicationStatus,
      nnglaPublicationOptions: { apiBaseUrl: resolvedApiBaseUrl, fetchRef },
    });
    setAuthorityState(viewport, statusNode, visibleStatusNode, {
      status: featureRuntime?.status === "READY" ? "READY" : "DEGRADED",
      message: `Authoritative NoveGeo boundary v${boundaryPublication.boundaryVersion} loaded from PostgreSQL-backed API.`,
      boundaryVersion: boundaryPublication.boundaryVersion,
    });
    return Object.freeze({ status: featureRuntime?.status || "DEGRADED", boundaryPublication, featureRuntime });
  }).catch((error) => {
    if (!disconnected) {
      setAuthorityState(viewport, statusNode, visibleStatusNode, {
        status: "DEGRADED",
        message: "Live NoveGeo authority is unavailable. No bundled sovereign boundary has been substituted.",
      });
    }
    return Object.freeze({ status: "DEGRADED", reason: "live_boundary_read_failed", error: error?.message || String(error) });
  });

  return Object.freeze({
    status: "LOADING",
    apiBaseUrl: resolvedApiBaseUrl,
    ready,
    get featureRuntime() { return featureRuntime; },
    disconnect() {
      disconnected = true;
      featureRuntime?.disconnect?.();
    },
  });
}
