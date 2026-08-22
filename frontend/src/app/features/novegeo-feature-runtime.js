/** P006.UI.13 / Bundle 12E Omega — additive NoveGeo feature integration above locked P004-P006 map modules. */
import { mountMapPresentation } from "../../map/presentation/map-presentation.js";
import { mountPhysicalLandPresentation } from "../../map/environment/physical-land-presentation.js";
import { mountBiospherePresentation } from "../../map/environment/biosphere-presentation.js";
import { mountHydrologyAtmospherePresentation } from "../../map/environment/hydrology-atmosphere-presentation.js";
import { mountFullViewportCoordinatePresentation } from "../../map/environment/full-viewport-coordinate-presentation.js";
import { mountMapNavigationDiscovery } from "../../map/interaction/map-navigation-discovery.js";
import { mountP006StateIntegration } from "../../map/state/p006-state-integration.js";
import { mountNnglaPublicationStatus } from "../../map/nngla/publication-status.js";
import { registerMapForegroundRecovery } from "../../map/lifecycle/foreground-recovery.js";
import {
  applyDefaultNoveGeoOpeningView,
  createNoveGeoResizeCoordinator,
} from "./novegeo-feature-geometry.js";

function button(documentRef, label, title, action) {
  const node = documentRef.createElement("button");
  node.type = "button";
  node.className = "novegeo-tool-button";
  node.setAttribute("aria-label", title);
  node.setAttribute("title", title);
  node.dataset.novegeoTool = action;
  node.textContent = label;
  return node;
}

function configureAdaptiveControls(documentRef) {
  const controls = documentRef.querySelector?.("[data-role='novegeo-map-discovery-controls']");
  const rail = documentRef.querySelector?.("[data-role='novegeo-tool-rail']");
  if (!controls || !rail || typeof documentRef.createElement !== "function") return Object.freeze({ status: "UNAVAILABLE" });

  controls.classList?.add?.("novegeo-feature-controls");
  controls.dataset.openPanel = "false";
  const tools = [
    ["−", "Zoom out", "zoom-out"],
    ["+", "Zoom in", "zoom-in"],
    ["⌕", "Coordinate search", "search"],
    ["◫", "Layers", "layers"],
    ["ⓘ", "Legend and map status", "info"],
    ["↺", "Reset map view", "reset"],
  ];
  for (const [label, title, action] of tools) rail.appendChild(button(documentRef, label, title, action));

  const openPanel = (panel) => {
    controls.dataset.openPanel = controls.dataset.openPanel === panel ? "false" : panel;
    controls.setAttribute?.("aria-hidden", String(controls.dataset.openPanel === "false"));
  };

  const onClick = (event) => {
    const tool = event.target?.closest?.("[data-novegeo-tool]");
    if (!tool) return;
    const action = tool.dataset.novegeoTool;
    if (["zoom-in", "zoom-out", "reset"].includes(action)) {
      controls.querySelector?.(`[data-map-action='${action}']`)?.click?.();
      return;
    }
    openPanel(action);
    if (action === "search") controls.querySelector?.("[data-role='novegeo-coordinate-search'] input")?.focus?.();
  };
  rail.addEventListener?.("click", onClick);

  const onEscape = (event) => {
    if (event.key === "Escape") controls.dataset.openPanel = "false";
  };
  documentRef.addEventListener?.("keydown", onEscape);

  return Object.freeze({
    status: "READY",
    disconnect() {
      rail.removeEventListener?.("click", onClick);
      documentRef.removeEventListener?.("keydown", onEscape);
    },
  });
}

export function mountNoveGeoFeatureRuntime({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  runtimeMode = "simulation",
  boundaryPublication = null,
  nnglaPublicationMount = mountNnglaPublicationStatus,
  nnglaPublicationOptions = {},
} = {}) {
  const viewport = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  if (!viewport) return Object.freeze({ status: "UNAVAILABLE", reason: "feature_viewport_missing" });

  // Bundle 12E Omega owns feature-page resize reconciliation so every P004/P005
  // presentation is redrawn against the same actual drawable viewport width.
  const base = boundaryPublication
    ? mountMapPresentation(documentRef, { observeResize: false, publication: boundaryPublication })
    : mountMapPresentation(documentRef, { observeResize: false });
  let physical = boundaryPublication
    ? mountPhysicalLandPresentation(documentRef, { boundaryPublication })
    : mountPhysicalLandPresentation(documentRef);
  let biosphere = boundaryPublication
    ? mountBiospherePresentation(documentRef, { boundaryPublication })
    : mountBiospherePresentation(documentRef);
  let hydroClimate = boundaryPublication
    ? mountHydrologyAtmospherePresentation(documentRef, { boundaryPublication })
    : mountHydrologyAtmospherePresentation(documentRef);
  let coordinates = boundaryPublication
    ? mountFullViewportCoordinatePresentation(documentRef, { boundaryPublication })
    : mountFullViewportCoordinatePresentation(documentRef);
  const discovery = boundaryPublication
    ? mountMapNavigationDiscovery(documentRef, windowRef, { publication: boundaryPublication })
    : mountMapNavigationDiscovery(documentRef, windowRef);
  const state = mountP006StateIntegration({ documentRef, windowRef, discovery, runtimeMode });
  const openingView = applyDefaultNoveGeoOpeningView({ viewport, discovery, stateIntegration: state });
  const adaptiveControls = configureAdaptiveControls(documentRef);
  const nnglaPublication = nnglaPublicationMount({ documentRef, fetchRef: windowRef?.fetch || globalThis.fetch, ...nnglaPublicationOptions });

  const redrawFeatureSurface = () => {
    const baseReceipt = base.redraw?.() || base;
    physical = boundaryPublication ? mountPhysicalLandPresentation(documentRef, { boundaryPublication }) : mountPhysicalLandPresentation(documentRef);
    biosphere = boundaryPublication ? mountBiospherePresentation(documentRef, { boundaryPublication }) : mountBiospherePresentation(documentRef);
    hydroClimate = boundaryPublication ? mountHydrologyAtmospherePresentation(documentRef, { boundaryPublication }) : mountHydrologyAtmospherePresentation(documentRef);
    coordinates = boundaryPublication ? mountFullViewportCoordinatePresentation(documentRef, { boundaryPublication }) : mountFullViewportCoordinatePresentation(documentRef);
    return Object.freeze({ base: baseReceipt, physical, biosphere, hydroClimate, coordinates });
  };

  const resize = createNoveGeoResizeCoordinator({
    viewport,
    windowRef,
    discovery,
    redraw: redrawFeatureSurface,
  });

  const recovery = registerMapForegroundRecovery({
    documentRef,
    windowRef,
    redrawMap: redrawFeatureSurface,
    redrawPhysicalLand: () => physical,
  });

  return Object.freeze({
    status: [base.status, physical.status, biosphere.status, hydroClimate.status, coordinates.status].every((value) => value === "RENDERED" || value === "READY")
      ? "READY"
      : "DEGRADED",
    runtimeMode,
    base,
    get physical() { return physical; },
    get biosphere() { return biosphere; },
    get hydroClimate() { return hydroClimate; },
    get coordinates() { return coordinates; },
    discovery,
    state,
    openingView,
    nnglaPublication,
    resize,
    disconnect() {
      resize.disconnect?.();
      discovery.disconnect?.();
      state.disconnect?.();
      adaptiveControls.disconnect?.();
      recovery.disconnect?.();
      nnglaPublication.disconnect?.();
      base.disconnect?.();
    },
  });
}
