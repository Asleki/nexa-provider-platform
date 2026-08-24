/** P006.7.11.15.0 / Bundle 22A — additive national-map shell hardening above locked map/runtime contracts. */
import { createNationalLayerStatus } from "./national-layer-status.js";
import { qualifyMapShellSafeArea } from "../validation/map-shell-safe-area.js";

export const BUNDLE22A_MAP_SHELL_VERSION = "bundle22a-v1";
export const BUNDLE22A_STYLE_HREF = "./styles/novegeo-map-shell-v1.css";
export const BUNDLE22A_MAP_NOTE = "Published NNGLA geography only. Unpublished canonical records remain hidden; reference layers and developer diagnostics do not assert public national features.";

function element(documentRef, tag, attrs = {}, text = "") {
  const node = documentRef.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (name === "className") node.className = value;
    else if (name === "dataset") Object.assign(node.dataset || {}, value);
    else node.setAttribute?.(name, value);
  }
  if (text) node.textContent = text;
  return node;
}

function ensureStylesheet(documentRef) {
  const existing = documentRef.querySelector?.("link[data-bundle22a-map-shell-style='true']");
  if (existing) return existing;
  if (!documentRef.createElement || !documentRef.head?.appendChild) return null;
  const link = documentRef.createElement("link");
  link.rel = "stylesheet";
  link.href = BUNDLE22A_STYLE_HREF;
  link.dataset.bundle22aMapShellStyle = "true";
  documentRef.head.appendChild(link);
  return link;
}

export function summarizeAuthorityState({ status = "UNKNOWN", boundaryVersion = null } = {}) {
  const normalized = String(status || "UNKNOWN").toUpperCase();
  if (normalized === "READY") {
    return boundaryVersion
      ? `✓ Live NNGLA authority · Boundary v${boundaryVersion}`
      : "✓ Live NNGLA authority";
  }
  if (normalized === "LOADING") return "Connecting to live NNGLA authority…";
  if (normalized === "DEGRADED") return "⚠ Live NNGLA authority unavailable · no static authority substituted";
  if (normalized === "DISCONNECTED") return "NNGLA authority disconnected";
  return "NNGLA authority state unavailable";
}

function createToolbar(documentRef, page, stage, rail) {
  let toolbar = page.querySelector?.("[data-role='novegeo-map-shell-toolbar']");
  if (toolbar) return toolbar;
  toolbar = element(documentRef, "div", {
    className: "novegeo-map-shell-toolbar",
    "data-role": "novegeo-map-shell-toolbar",
    "aria-label": "NoveGeo map controls",
  });
  const identity = element(documentRef, "div", { className: "novegeo-map-shell-toolbar-copy" });
  identity.append?.(
    element(documentRef, "strong", {}, "National map"),
    element(documentRef, "span", {}, "Reference tools · publication-gated national layers"),
  );
  toolbar.append?.(identity);
  if (rail) toolbar.append?.(rail);
  stage.parentNode?.insertBefore?.(toolbar, stage);
  if (!toolbar.parentNode && page.insertBefore) page.insertBefore(toolbar, stage);
  return toolbar;
}

function createNationalLayerSection(documentRef) {
  const section = element(documentRef, "section", {
    className: "novegeo-national-layer-status",
    "data-role": "novegeo-national-layer-status",
    "aria-label": "National geography layer readiness",
  });
  section.append?.(
    element(documentRef, "strong", {}, "National geography"),
    element(documentRef, "p", {}, "Reserved governed layer families. They remain disabled until their publication/read milestones make them map-renderable."),
  );
  const list = element(documentRef, "ul", { className: "novegeo-national-layer-list" });
  for (const layer of createNationalLayerStatus()) {
    const item = element(documentRef, "li", { "data-national-layer-key": layer.key });
    item.append?.(
      element(documentRef, "span", {}, layer.label),
      element(documentRef, "small", { "data-layer-availability": layer.availability }, layer.statusLabel),
    );
    list.append?.(item);
  }
  section.append?.(list);
  const search = element(documentRef, "p", { className: "novegeo-national-search-reservation", "data-role": "novegeo-national-search-reservation" }, "National feature search is reserved for P006.7.11.15.9. Coordinate search remains available as a reference tool.");
  section.append?.(search);
  return section;
}

function ensureDeveloperDetails(documentRef, page) {
  let details = page.querySelector?.("[data-role='novegeo-developer-details']");
  if (details) return details;
  details = element(documentRef, "details", { className: "novegeo-developer-details", "data-role": "novegeo-developer-details" });
  details.append?.(element(documentRef, "summary", {}, "Developer & authority details"));
  const body = element(documentRef, "div", { className: "novegeo-developer-details-body", "data-role": "novegeo-developer-details-body" });
  body.append?.(element(documentRef, "p", { "data-role": "novegeo-developer-details-placeholder" }, "Detailed PostgreSQL publication diagnostics appear here when the live NNGLA status endpoint is available."));
  details.append?.(body);
  page.append?.(details);
  return details;
}

function updateCurrentWording(page) {
  const note = page.querySelector?.(".novegeo-feature-note");
  if (note) note.textContent = BUNDLE22A_MAP_NOTE;
}

function updateAuthoritySummary(page) {
  const viewport = page.querySelector?.("[data-role='future-map-viewport']");
  const statusNode = page.querySelector?.("[data-role='novegeo-authority-state']");
  if (!viewport || !statusNode) return;
  statusNode.classList?.add?.("novegeo-authority-summary");
  statusNode.textContent = summarizeAuthorityState({
    status: viewport.dataset?.authorityStatus,
    boundaryVersion: viewport.dataset?.authorityBoundaryVersion,
  });
}

function trimPermanentTools(documentRef, rail) {
  if (!rail) return null;
  const buttons = Array.from(rail.querySelectorAll?.("[data-novegeo-tool]") || []);
  let toolsButton = buttons.find((button) => button.dataset?.novegeoTool === "tools") || null;
  for (const button of buttons) {
    const action = button.dataset?.novegeoTool;
    if (action === "zoom-out" || action === "zoom-in" || action === "tools") continue;
    if (!toolsButton && action === "layers") {
      button.dataset.novegeoTool = "tools";
      button.textContent = "☰";
      button.setAttribute?.("aria-label", "Map tools");
      button.setAttribute?.("title", "Map tools");
      button.setAttribute?.("aria-expanded", "false");
      button.classList?.add?.("novegeo-tools-button");
      toolsButton = button;
      continue;
    }
    button.remove?.();
  }
  if (!toolsButton && typeof documentRef?.createElement === "function") {
    toolsButton = element(documentRef, "button", {
      type: "button",
      className: "novegeo-tool-button novegeo-tools-button",
      "data-novegeo-tool": "tools",
      "aria-label": "Map tools",
      title: "Map tools",
      "aria-expanded": "false",
    }, "☰");
    rail.append?.(toolsButton);
  }
  rail.dataset.bundle22aCompact = "true";
  return toolsButton;
}

function prepareToolPanel(documentRef, page) {
  const controls = page.querySelector?.("[data-role='novegeo-map-discovery-controls']");
  if (!controls) return null;
  controls.classList?.add?.("novegeo-map-tools-sheet");
  controls.setAttribute?.("aria-label", "NoveGeo map tools");
  const layers = controls.querySelector?.(".map-layer-controls");
  const legend = layers?.querySelector?.("legend");
  if (legend) legend.textContent = "Reference layers";
  const legendDetails = controls.querySelector?.(".map-legend");
  const legendSummary = legendDetails?.querySelector?.("summary");
  if (legendSummary) legendSummary.textContent = "Reference legend";
  const searchTitle = controls.querySelector?.("[data-role='novegeo-coordinate-search'] strong");
  if (searchTitle) searchTitle.textContent = "Coordinate search · reference";
  if (!controls.querySelector?.("[data-role='novegeo-map-tools-heading']")) {
    const heading = element(documentRef, "header", { className: "novegeo-map-tools-heading", "data-role": "novegeo-map-tools-heading" });
    heading.append?.(
      element(documentRef, "strong", {}, "Map tools"),
      element(documentRef, "span", {}, "Reference controls are active. National layers remain publication-gated."),
    );
    controls.insertBefore?.(heading, controls.firstChild || null);
  }
  if (!controls.querySelector?.("[data-role='novegeo-national-layer-status']")) {
    const national = createNationalLayerSection(documentRef);
    if (layers?.nextSibling) controls.insertBefore?.(national, layers.nextSibling);
    else controls.append?.(national);
  }
  return controls;
}

function moveDeveloperDiagnostics(page, details) {
  const panel = page.querySelector?.("[data-role='nngla-live-publication-status']");
  const body = details?.querySelector?.("[data-role='novegeo-developer-details-body']");
  if (!panel || !body || panel.parentNode === body) return false;
  body.querySelector?.("[data-role='novegeo-developer-details-placeholder']")?.remove?.();
  body.append?.(panel);
  return true;
}

function measureSafeArea(page, toolbar) {
  const viewport = page.querySelector?.("[data-role='future-map-viewport']");
  if (!viewport?.getBoundingClientRect || !toolbar?.getBoundingClientRect) return Object.freeze({ status: "UNMEASURED", overlapCount: 0, overlaps: Object.freeze([]) });
  const result = qualifyMapShellSafeArea({
    viewportRect: viewport.getBoundingClientRect(),
    permanentControlRects: [{ id: "map-shell-toolbar", rect: toolbar.getBoundingClientRect() }],
  });
  page.dataset.mapShellSafeArea = result.status;
  return result;
}

export function mountNoveGeoMapShell({ documentRef = globalThis.document, windowRef = globalThis.window } = {}) {
  const page = documentRef?.querySelector?.(".novegeo-feature-page");
  const stage = page?.querySelector?.("[data-role='novegeo-map-stage']");
  const rail = page?.querySelector?.("[data-role='novegeo-tool-rail']");
  if (!page || !stage || !rail || typeof documentRef?.createElement !== "function") {
    return Object.freeze({ status: "UNAVAILABLE", reason: "novegeo_map_shell_missing", reconcile() {}, disconnect() {} });
  }

  ensureStylesheet(documentRef);
  page.dataset.mapShellVersion = BUNDLE22A_MAP_SHELL_VERSION;
  const toolbar = createToolbar(documentRef, page, stage, rail);
  const details = ensureDeveloperDetails(documentRef, page);
  updateCurrentWording(page);
  updateAuthoritySummary(page);

  let controls = null;
  let toolsButton = null;
  let listenersBound = false;

  const syncExpanded = () => {
    if (!toolsButton || !controls) return;
    toolsButton.setAttribute?.("aria-expanded", String(controls.dataset?.openPanel !== "false"));
  };

  const onToolbarClick = () => queueMicrotask(syncExpanded);
  const onKeydown = (event) => {
    if (event.key === "Escape") queueMicrotask(syncExpanded);
  };

  const reconcile = () => {
    toolsButton = trimPermanentTools(documentRef, rail) || toolsButton;
    controls = prepareToolPanel(documentRef, page) || controls;
    moveDeveloperDiagnostics(page, details);
    updateCurrentWording(page);
    updateAuthoritySummary(page);
    if (!listenersBound && toolsButton && controls) {
      rail.addEventListener?.("click", onToolbarClick);
      documentRef.addEventListener?.("keydown", onKeydown);
      listenersBound = true;
    }
    syncExpanded();
    return Object.freeze({ status: "READY", safeArea: measureSafeArea(page, toolbar) });
  };

  const onResize = () => measureSafeArea(page, toolbar);
  windowRef?.addEventListener?.("resize", onResize);
  const initial = reconcile();

  return Object.freeze({
    status: "READY",
    version: BUNDLE22A_MAP_SHELL_VERSION,
    initial,
    reconcile,
    disconnect() {
      windowRef?.removeEventListener?.("resize", onResize);
      if (listenersBound) {
        rail.removeEventListener?.("click", onToolbarClick);
        documentRef.removeEventListener?.("keydown", onKeydown);
      }
    },
  });
}
