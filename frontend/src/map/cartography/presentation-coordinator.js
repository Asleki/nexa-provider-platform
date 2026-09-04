/**
 * P006.7.11.15.10.1 — NoveGeo styling architecture lock coordinator.
 *
 * Layout ownership, renderer ownership and governed data completeness are
 * deliberately independent. MAP_FIRST begins when the NoveGeo viewport mounts;
 * UNIFIED begins when the authoritative boundary can render a base frame;
 * governed layers then arrive progressively without fabricating missing facts.
 */
import { createNoveGeoCountryLabelCandidate } from "./country-anchor.js";
import { renderUnifiedCartographicFrame, UNIFIED_CANVAS_ROLE } from "./unified-frame-renderer.js";
import { REQUIRED_LAYER_KEYS } from "./unified-frame-plan.js";
import { UnifiedLayerKey } from "./semantic-zoom-v2.js";

export const NOVEGEO_PRESENTATION_COORDINATOR_ID = "presentation:novegeo:map-first-coordinator";
export const NOVEGEO_PRESENTATION_COORDINATOR_VERSION = 2;
export const NOVEGEO_MAP_FIRST_STYLE_HREF = "./styles/novegeo-map-first-v1.css";

export const LayoutMode = Object.freeze({ LEGACY: "LEGACY", MAP_FIRST: "MAP_FIRST" });
export const PresentationMode = Object.freeze({ LEGACY: "LEGACY", UNIFIED: "UNIFIED" });
export const DataState = Object.freeze({ LOADING: "LOADING", PARTIAL: "PARTIAL", READY: "READY", DEGRADED: "DEGRADED" });

function ensureStylesheet(documentRef) {
  const existing = documentRef?.querySelector?.("link[data-novegeo-map-first-style='true']");
  if (existing) return existing;
  if (!documentRef?.createElement || !documentRef?.head?.appendChild) return null;
  const link = documentRef.createElement("link");
  link.rel = "stylesheet";
  link.href = NOVEGEO_MAP_FIRST_STYLE_HREF;
  link.dataset.novegeoMapFirstStyle = "true";
  documentRef.head.appendChild(link);
  return link;
}

function measuredViewport(viewport) {
  const rect = viewport?.getBoundingClientRect?.();
  const width = Number(rect?.width || viewport?.clientWidth || 0);
  const height = Number(rect?.height || viewport?.clientHeight || 0);
  if (!(Number.isFinite(width) && width > 0 && Number.isFinite(height) && height > 0)) {
    throw new RangeError("map-first viewport has no positive drawable dimensions");
  }
  return { width, height };
}

function mapFirstTargetDimensions(viewport, windowRef) {
  const measured = measuredViewport(viewport);
  const visualWidth = Number(windowRef?.visualViewport?.width || 0);
  const visualHeight = Number(windowRef?.visualViewport?.height || 0);
  const innerWidth = Number(windowRef?.innerWidth || 0);
  const innerHeight = Number(windowRef?.innerHeight || 0);
  const width = visualWidth > 0 ? visualWidth : innerWidth > 0 ? innerWidth : measured.width;
  const height = visualHeight > 0 ? visualHeight : innerHeight > 0 ? innerHeight : measured.height;
  return Object.freeze({ width, height });
}

export function parseLegacyNavigation(viewport) {
  const base = viewport?.querySelector?.("[data-role='novegeo-map-canvas']");
  const fallbackZoom = Number(viewport?.dataset?.mapZoom || 1);
  const transform = String(base?.style?.transform || "");
  const match = transform.match(/translate\(\s*(-?[\d.]+)px\s*,\s*(-?[\d.]+)px\s*\)\s*scale\(\s*([\d.]+)\s*\)/);
  if (match) {
    return Object.freeze({ zoom: Number(match[3]), offsetX: Number(match[1]), offsetY: Number(match[2]) });
  }
  return Object.freeze({
    zoom: Number.isFinite(fallbackZoom) && fallbackZoom > 0 ? fallbackZoom : 1,
    offsetX: 0,
    offsetY: 0,
  });
}

function immutableSnapshot({ layerKey, items, candidates, readRuntime, semanticChecksum }) {
  if (!REQUIRED_LAYER_KEYS.includes(layerKey)) throw new Error(`unsupported unified layer snapshot: ${layerKey}`);
  if (!Array.isArray(items) || !Array.isArray(candidates)) throw new TypeError("layer snapshot items and candidates must be arrays");
  return Object.freeze({
    layerKey,
    items: Object.freeze([...items]),
    candidates: Object.freeze([...candidates]),
    readRuntime: readRuntime || null,
    semanticChecksum: semanticChecksum || null,
  });
}

function resolveDataState(snapshots, degradedLayers) {
  if (degradedLayers.size > 0) return DataState.DEGRADED;
  if (REQUIRED_LAYER_KEYS.every((key) => snapshots.has(key))) return DataState.READY;
  if (snapshots.size > 0) return DataState.PARTIAL;
  return DataState.LOADING;
}

function setPresentationDataset(documentRef, page, viewport, { rendererMode, layoutMode, dataState }) {
  for (const node of [page, viewport, documentRef?.querySelector?.("#nexilabs-app")]) {
    if (!node?.dataset) continue;
    node.dataset.novegeoPresentationMode = rendererMode;
    node.dataset.novegeoLayoutMode = layoutMode;
    node.dataset.novegeoDataState = dataState;
  }
}

function ensureUnifiedCanvas(documentRef, viewport) {
  let canvas = viewport.querySelector?.(`[data-role='${UNIFIED_CANVAS_ROLE}']`);
  if (!canvas) {
    canvas = documentRef.createElement("canvas");
    canvas.setAttribute("data-role", UNIFIED_CANVAS_ROLE);
    canvas.setAttribute("aria-hidden", "true");
    viewport.appendChild?.(canvas);
  }
  Object.assign(canvas.style || {}, { visibility: "hidden", opacity: "1" });
  return canvas;
}

function ensureScaleNode(documentRef, viewport) {
  let node = viewport.querySelector?.("[data-role='novegeo-unified-distance-scale']");
  if (node) return node;
  node = documentRef.createElement("div");
  node.className = "novegeo-unified-distance-scale";
  node.setAttribute("data-role", "novegeo-unified-distance-scale");
  node.setAttribute("aria-label", "Approximate map distance scale");
  const bar = documentRef.createElement("span");
  bar.className = "novegeo-unified-distance-scale-bar";
  bar.setAttribute("data-role", "novegeo-unified-distance-scale-bar");
  const labels = documentRef.createElement("span");
  labels.className = "novegeo-unified-distance-scale-labels";
  labels.setAttribute("data-role", "novegeo-unified-distance-scale-labels");
  node.append?.(bar, labels);
  viewport.appendChild?.(node);
  return node;
}

function updateScaleNode(node, scale) {
  if (!node || !scale) return;
  const bar = node.querySelector?.("[data-role='novegeo-unified-distance-scale-bar']");
  const labels = node.querySelector?.("[data-role='novegeo-unified-distance-scale-labels']");
  if (bar?.style) bar.style.width = `${scale.widthPx}px`;
  if (labels) labels.textContent = `${scale.metricLabel} · ${scale.imperialLabel}`;
  node.hidden = false;
}

export function createNoveGeoPresentationCoordinator({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  preferredMode = PresentationMode.UNIFIED,
  renderFrameRef = renderUnifiedCartographicFrame,
} = {}) {
  if (!Object.values(PresentationMode).includes(preferredMode)) throw new Error(`unsupported presentation mode: ${preferredMode}`);
  ensureStylesheet(documentRef);

  let mode = PresentationMode.LEGACY;
  let layoutMode = LayoutMode.LEGACY;
  let dataState = DataState.LOADING;
  let page = null;
  let viewport = null;
  let boundaryPublication = null;
  let countryCandidate = null;
  let unifiedCanvas = null;
  let scaleNode = null;
  let previousBand = null;
  let presentationRevision = 0;
  let latestReceipt = null;
  let observers = [];
  let legacyVisibility = [];
  let legacyOverlayVisibility = [];
  const snapshots = new Map();
  const degradedLayers = new Map();
  const userLayerVisibility = {
    [UnifiedLayerKey.COUNTRY]: true,
    [UnifiedLayerKey.REGION]: true,
    [UnifiedLayerKey.CITY]: true,
    [UnifiedLayerKey.MUNICIPALITY]: true,
    [UnifiedLayerKey.CITY_DISTRICT]: true,
    [UnifiedLayerKey.TOWN]: true,
    [UnifiedLayerKey.REFERENCE]: true,
  };

  const presentationRoles = Object.freeze({});

  const publishState = () => setPresentationDataset(documentRef, page, viewport, { rendererMode: mode, layoutMode, dataState });
  const refreshDataState = () => { dataState = resolveDataState(snapshots, degradedLayers); publishState(); return dataState; };

  const detachObservers = () => {
    for (const disconnect of observers.splice(0)) disconnect?.();
  };

  const rememberAndHideLegacy = () => {
    legacyVisibility = [];
    for (const node of viewport?.querySelectorAll?.("canvas[data-role]") || []) {
      if (node === unifiedCanvas || node.dataset?.role === UNIFIED_CANVAS_ROLE) continue;
      legacyVisibility.push({ node, visibility: node.style?.visibility || "" });
      if (node.style) node.style.visibility = "hidden";
    }
    legacyOverlayVisibility = [];
    for (const selector of ["[data-role='novegeo-equator-label']", "[data-role='novegeo-selection-marker']"]) {
      const node = viewport?.querySelector?.(selector);
      if (!node) continue;
      legacyOverlayVisibility.push({ node, visibility: node.style?.visibility || "" });
      if (node.style) node.style.visibility = "hidden";
    }
  };

  const restoreLegacyNodes = () => {
    for (const entry of legacyVisibility) if (entry.node?.style) entry.node.style.visibility = entry.visibility;
    for (const entry of legacyOverlayVisibility) if (entry.node?.style) entry.node.style.visibility = entry.visibility;
    legacyVisibility = [];
    legacyOverlayVisibility = [];
  };

  const setMode = (nextMode) => {
    mode = nextMode;
    publishState();
  };

  const rollbackToLegacy = (reason = "unified_frame_failed") => {
    restoreLegacyNodes();
    if (unifiedCanvas?.style) unifiedCanvas.style.visibility = "hidden";
    if (scaleNode) scaleNode.hidden = true;
    previousBand = null;
    setMode(PresentationMode.LEGACY);
    latestReceipt = Object.freeze({
      status: "RENDERER_LEGACY_RESTORED",
      reason,
      presentationRevision,
      layoutMode,
      dataState,
      activePresentationMode: PresentationMode.LEGACY,
    });
    return latestReceipt;
  };

  const renderCandidateFrame = ({ preserveGeographicCenter = false, prepareMapFirstViewport = false } = {}) => {
    if (!viewport || !boundaryPublication || !countryCandidate) {
      return Object.freeze({ status: "WAITING_FOR_AUTHORITY_BOUNDARY" });
    }
    const dimensions = prepareMapFirstViewport
      ? mapFirstTargetDimensions(viewport, windowRef)
      : measuredViewport(viewport);
    unifiedCanvas = ensureUnifiedCanvas(documentRef, viewport);
    scaleNode = ensureScaleNode(documentRef, viewport);
    scaleNode.hidden = true;
    const navigation = parseLegacyNavigation(viewport);
    const navigationRevision = Number(viewport.dataset?.mapNavigationRevision || 0);
    const snapshotObject = Object.freeze(Object.fromEntries([...snapshots.entries()]));
    const snapshotSources = Object.freeze(Object.fromEntries([...snapshots.entries()].map(([key, snapshot]) => [key, Object.freeze({
      readRuntime: snapshot.readRuntime,
      semanticChecksum: snapshot.semanticChecksum,
      itemCount: snapshot.items.length,
      candidateCount: snapshot.candidates.length,
    })])));
    const frame = renderFrameRef({
      canvas: unifiedCanvas,
      cssWidth: dimensions.width,
      cssHeight: dimensions.height,
      devicePixelRatio: Number(windowRef?.devicePixelRatio || globalThis.devicePixelRatio || 1),
      boundaryPublication,
      countryCandidate,
      snapshots: snapshotObject,
      zoom: navigation.zoom,
      navigation,
      previousBand,
      userLayerVisibility,
      presentationRoles,
      preserveGeographicCenter: preserveGeographicCenter ? latestReceipt?.geographicCenter || null : null,
    });
    if (frame?.status !== "RENDERED") throw new Error("unified frame did not render completely");
    previousBand = frame.semanticBand;
    presentationRevision += 1;
    return Object.freeze({
      ...frame,
      presentationCoordinatorId: NOVEGEO_PRESENTATION_COORDINATOR_ID,
      presentationCoordinatorVersion: NOVEGEO_PRESENTATION_COORDINATOR_VERSION,
      presentationRevision,
      navigationRevision,
      layoutMode,
      dataState,
      activePresentationMode: PresentationMode.UNIFIED,
      authorityBoundary: Object.freeze({
        boundaryId: boundaryPublication.boundaryId || null,
        boundaryVersion: boundaryPublication.boundaryVersion || null,
        publicationId: boundaryPublication.publicationId || null,
      }),
      degradedLayers: Object.freeze([...degradedLayers.keys()].sort()),
      snapshotSources,
    });
  };

  const activate = () => {
    if (preferredMode !== PresentationMode.UNIFIED) return Object.freeze({ status: "LEGACY_SELECTED", activePresentationMode: mode, layoutMode, dataState });
    if (!boundaryPublication || !viewport) {
      return Object.freeze({ status: "WAITING_FOR_AUTHORITY_BOUNDARY", activePresentationMode: mode, layoutMode, dataState });
    }
    try {
      const frame = renderCandidateFrame({ prepareMapFirstViewport: true });
      if (frame.status !== "RENDERED") return frame;
      rememberAndHideLegacy();
      if (unifiedCanvas?.style) unifiedCanvas.style.visibility = "visible";
      setMode(PresentationMode.UNIFIED);
      updateScaleNode(scaleNode, frame.scale);
      latestReceipt = frame;
      return frame;
    } catch (error) {
      return rollbackToLegacy(error?.message || String(error));
    }
  };

  const redraw = ({ preserveGeographicCenter = false } = {}) => {
    if (mode !== PresentationMode.UNIFIED) return activate();
    try {
      const frame = renderCandidateFrame({ preserveGeographicCenter });
      if (frame.status !== "RENDERED") return frame;
      if (unifiedCanvas?.style) unifiedCanvas.style.visibility = "visible";
      updateScaleNode(scaleNode, frame.scale);
      latestReceipt = frame;
      return frame;
    } catch (error) {
      return rollbackToLegacy(error?.message || String(error));
    }
  };

  const attachViewport = ({ documentRef: nextDocument = documentRef, windowRef: nextWindow = windowRef } = {}) => {
    const nextPage = nextDocument?.querySelector?.(".novegeo-feature-page");
    const nextViewport = nextPage?.querySelector?.("[data-role='future-map-viewport']")
      || nextDocument?.querySelector?.("[data-role='future-map-viewport']");
    if (!nextPage || !nextViewport) return Object.freeze({ status: "UNAVAILABLE", reason: "map_viewport_missing" });

    if (viewport && viewport !== nextViewport) {
      restoreLegacyNodes();
      detachObservers();
      snapshots.clear();
      degradedLayers.clear();
      boundaryPublication = null;
      countryCandidate = null;
      previousBand = null;
      unifiedCanvas = null;
      scaleNode = null;
      mode = PresentationMode.LEGACY;
      dataState = DataState.LOADING;
    }

    page = nextPage;
    viewport = nextViewport;
    layoutMode = LayoutMode.MAP_FIRST;
    refreshDataState();
    if (observers.length) return Object.freeze({ status: "READY", reused: true, layoutMode, dataState, activePresentationMode: mode });

    const schedule = (preserveGeographicCenter = false) => {
      const run = () => { if (mode === PresentationMode.UNIFIED) redraw({ preserveGeographicCenter }); };
      if (typeof nextWindow?.requestAnimationFrame === "function") nextWindow.requestAnimationFrame(run);
      else queueMicrotask(run);
    };
    const scheduleResize = () => schedule(true);
    const scheduleNavigation = () => schedule(false);

    const ResizeObserverCtor = nextWindow?.ResizeObserver || globalThis.ResizeObserver;
    if (typeof ResizeObserverCtor === "function") {
      const observer = new ResizeObserverCtor(scheduleResize);
      observer.observe(viewport);
      observers.push(() => observer.disconnect?.());
    }
    const MutationObserverCtor = nextWindow?.MutationObserver || globalThis.MutationObserver;
    if (typeof MutationObserverCtor === "function") {
      const observer = new MutationObserverCtor(scheduleNavigation);
      observer.observe(viewport, { attributes: true, attributeFilter: ["data-map-zoom", "data-map-navigation-revision"] });
      observers.push(() => observer.disconnect?.());

      const statusAttributes = Object.freeze({
        "data-novegeo-region-map-status": UnifiedLayerKey.REGION,
        "data-novegeo-city-map-status": UnifiedLayerKey.CITY,
        "data-novegeo-municipality-map-status": UnifiedLayerKey.MUNICIPALITY,
        "data-novegeo-city-district-map-status": UnifiedLayerKey.CITY_DISTRICT,
        "data-novegeo-town-map-status": UnifiedLayerKey.TOWN,
      });
      const statusObserver = new MutationObserverCtor((records = []) => {
        for (const record of records) {
          const layerKey = statusAttributes[record.attributeName];
          if (!layerKey) continue;
          const status = String(record.target?.getAttribute?.(record.attributeName) || "").toUpperCase();
          if (status === "DEGRADED") degradedLayers.set(layerKey, "layer_runtime_degraded");
          else if (status === "READY" || status === "RENDERED") degradedLayers.delete(layerKey);
        }
        refreshDataState();
      });
      statusObserver.observe(page, { attributes: true, attributeFilter: Object.keys(statusAttributes) });
      observers.push(() => statusObserver.disconnect?.());
    }
    const visualViewport = nextWindow?.visualViewport;
    visualViewport?.addEventListener?.("resize", scheduleResize);
    if (visualViewport) observers.push(() => visualViewport.removeEventListener?.("resize", scheduleResize));
    nextWindow?.addEventListener?.("orientationchange", scheduleResize);
    observers.push(() => nextWindow?.removeEventListener?.("orientationchange", scheduleResize));
    nextWindow?.addEventListener?.("resize", scheduleResize);
    observers.push(() => nextWindow?.removeEventListener?.("resize", scheduleResize));

    const onLayerChange = (event) => {
      const key = event?.target?.dataset?.layerKey;
      if (key === "coordinates") {
        userLayerVisibility[UnifiedLayerKey.REFERENCE] = event.target.checked !== false;
        if (mode === PresentationMode.UNIFIED) redraw();
      }
    };
    nextDocument?.addEventListener?.("change", onLayerChange);
    observers.push(() => nextDocument?.removeEventListener?.("change", onLayerChange));

    return Object.freeze({ status: "READY", layoutMode, dataState, activePresentationMode: mode });
  };

  return Object.freeze({
    coordinatorId: NOVEGEO_PRESENTATION_COORDINATOR_ID,
    coordinatorVersion: NOVEGEO_PRESENTATION_COORDINATOR_VERSION,
    preferredMode,
    get mode() { return mode; },
    get layoutMode() { return layoutMode; },
    get dataState() { return dataState; },
    get latestReceipt() { return latestReceipt; },
    attachViewport,
    bindBoundary(publication) {
      if (!publication?.extent || !publication?.geometry) throw new TypeError("authoritative boundary publication is required");
      boundaryPublication = publication;
      countryCandidate = createNoveGeoCountryLabelCandidate(publication, { countryId: "country:novegeo", displayName: "NoveGeo" });
      return mode === PresentationMode.UNIFIED ? redraw() : activate();
    },
    registerLayerSnapshot(input = {}) {
      const snapshot = immutableSnapshot(input);
      snapshots.set(snapshot.layerKey, snapshot);
      degradedLayers.delete(snapshot.layerKey);
      refreshDataState();
      const activation = mode === PresentationMode.UNIFIED ? redraw() : activate();
      return Object.freeze({
        status: "REGISTERED",
        layerKey: snapshot.layerKey,
        itemCount: snapshot.items.length,
        candidateCount: snapshot.candidates.length,
        registeredLayerCount: snapshots.size,
        requiredLayerCount: REQUIRED_LAYER_KEYS.length,
        layoutMode,
        dataState,
        activePresentationMode: mode,
        activation,
      });
    },
    markLayerDegraded(layerKey, reason = "layer_read_failed") {
      if (!REQUIRED_LAYER_KEYS.includes(layerKey)) throw new Error(`unsupported unified layer snapshot: ${layerKey}`);
      degradedLayers.set(layerKey, String(reason));
      refreshDataState();
      return Object.freeze({ status: "LAYER_DEGRADED", layerKey, reason: String(reason), layoutMode, dataState, activePresentationMode: mode });
    },
    setLayerEnabled(layerKey, value) {
      if (!(layerKey in userLayerVisibility)) throw new Error(`unknown presentation layer: ${layerKey}`);
      userLayerVisibility[layerKey] = value !== false;
      return mode === PresentationMode.UNIFIED ? redraw() : Object.freeze({ status: "LEGACY", layoutMode, dataState, activePresentationMode: mode });
    },
    redraw,
    restoreLegacy(reason = "manual_restore") { return rollbackToLegacy(reason); },
    disconnect() {
      detachObservers();
      restoreLegacyNodes();
      if (unifiedCanvas?.style) unifiedCanvas.style.visibility = "hidden";
      if (scaleNode) scaleNode.hidden = true;
      mode = PresentationMode.LEGACY;
      layoutMode = LayoutMode.LEGACY;
      dataState = DataState.LOADING;
      publishState();
    },
  });
}
