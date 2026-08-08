/** Bundle 12A — P006.1-P006.3 interactive navigation, controls and coordinate discovery. */
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../presentation/publication.js";
import { createMapNavigationController } from "./navigation-controller.js";
import { bindMapNavigationInputs } from "./input-bindings.js";
import { MAP_LAYER_CATALOG, createLayerVisibility, applyLayerVisibility } from "../controls/layer-state.js";
import { createScaleModel } from "../controls/scale.js";
import { resolveCoordinateSearch, viewportPointToCoordinate } from "../selection/coordinate-search.js";
import { coordinateToViewportPoint } from "../selection/location-selection.js";

const CONTROL_ROLE = "novegeo-map-discovery-controls";
const EQUATOR_ROLE = "novegeo-equator-label";
const MARKER_ROLE = "novegeo-selection-marker";

export function calculateEquatorLabelY({ extent, height, padding = 0, navigationState }) {
  const h = Number(height);
  const inset = Number(padding);
  const drawableHeight = h - inset * 2;
  const baseY = inset + ((extent.maxLatitude - 0) / (extent.maxLatitude - extent.minLatitude)) * drawableHeight;
  const y = (baseY - h / 2) * navigationState.zoom + h / 2 + navigationState.offsetY;
  return Math.max(14, Math.min(h - 20, y));
}

function rectOf(element) {
  const rect = element.getBoundingClientRect?.();
  return { width: Number(rect?.width || element.clientWidth || 640), height: Number(rect?.height || element.clientHeight || 435) };
}

function element(documentRef, tag, attrs = {}, text = "") {
  const node = documentRef.createElement(tag);
  for (const [name, value] of Object.entries(attrs)) {
    if (name === "className") node.className = value;
    else node.setAttribute(name, value);
  }
  if (text) node.textContent = text;
  return node;
}

function createControls(documentRef) {
  const panel = element(documentRef, "section", { "data-role": CONTROL_ROLE, className: "map-discovery-controls", "aria-label": "NoveGeo map navigation and discovery controls" });
  const navigation = element(documentRef, "div", { className: "map-control-group" });
  navigation.append(element(documentRef, "strong", {}, "Navigate"));
  for (const [action, label] of [["zoom-out", "−"], ["reset", "Reset"], ["zoom-in", "+"]]) navigation.append(element(documentRef, "button", { type: "button", "data-map-action": action, "aria-label": action.replace("-", " ") }, label));
  panel.append(navigation);

  const layers = element(documentRef, "fieldset", { className: "map-control-group map-layer-controls" });
  layers.append(element(documentRef, "legend", {}, "Layers"));
  for (const layer of MAP_LAYER_CATALOG) {
    const label = element(documentRef, "label", { className: "map-layer-toggle" });
    const input = element(documentRef, "input", { type: "checkbox", "data-layer-key": layer.key });
    input.checked = true;
    label.append(input, documentRef.createTextNode?.(layer.label) || element(documentRef, "span", {}, layer.label));
    layers.append(label);
  }
  panel.append(layers);

  const legend = element(documentRef, "details", { className: "map-legend" });
  legend.append(element(documentRef, "summary", {}, "Legend"));
  const legendList = element(documentRef, "ul");
  for (const layer of MAP_LAYER_CATALOG) legendList.append(element(documentRef, "li", {}, `${layer.label}: ${layer.legend}`));
  legend.append(legendList);
  panel.append(legend);

  const scale = element(documentRef, "div", { className: "map-scale", "data-role": "novegeo-map-scale" });
  scale.append(element(documentRef, "span", { className: "map-scale-bar", "data-role": "novegeo-map-scale-bar" }), element(documentRef, "span", { "data-role": "novegeo-map-scale-label" }, "Scale"));
  panel.append(scale);

  const form = element(documentRef, "form", { className: "map-coordinate-search", "data-role": "novegeo-coordinate-search" });
  form.append(element(documentRef, "strong", {}, "Coordinate search"));
  form.append(element(documentRef, "label", {}, "Longitude"));
  form.append(element(documentRef, "input", { name: "longitude", type: "number", step: "any", inputmode: "decimal", required: "" }));
  form.append(element(documentRef, "label", {}, "Latitude"));
  form.append(element(documentRef, "input", { name: "latitude", type: "number", step: "any", inputmode: "decimal", required: "" }));
  form.append(element(documentRef, "button", { type: "submit" }, "Locate"));
  form.append(element(documentRef, "output", { "data-role": "novegeo-selection-status", "aria-live": "polite" }, "No location selected"));
  panel.append(form);
  return panel;
}

function ensureOverlay(documentRef, viewport, role, className, text = "") {
  let node = viewport.querySelector?.(`[data-role='${role}']`);
  if (!node) {
    node = element(documentRef, "div", { "data-role": role, className, "aria-hidden": "true" }, text);
    viewport.appendChild?.(node);
  }
  return node;
}

export function mountMapNavigationDiscovery(documentRef, windowRef = globalThis.window, { publication = BUNDLED_WORLD_BOUNDARY_PUBLICATION } = {}) {
  const viewport = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  if (!viewport || typeof documentRef?.createElement !== "function") return Object.freeze({ status: "UNAVAILABLE", reason: "viewport_missing" });
  if (viewport.dataset?.p006NavigationMounted === "true") return Object.freeze({ status: "READY", reused: true });

  if (viewport.dataset) viewport.dataset.p006NavigationMounted = "true";
  if (viewport.style) viewport.style.position = "relative";
  const equatorLabel = ensureOverlay(documentRef, viewport, EQUATOR_ROLE, "map-equator-label", "Equator · 0°");
  const marker = ensureOverlay(documentRef, viewport, MARKER_ROLE, "map-selection-marker");
  marker.hidden = true;

  const controls = createControls(documentRef);
  viewport.insertAdjacentElement?.("afterend", controls);
  if (!controls.parentNode && viewport.parentNode?.appendChild) viewport.parentNode.appendChild(controls);

  let visibility = createLayerVisibility();
  let selection = null;
  const extent = publication.extent;

  const renderScale = (state) => {
    const { width } = rectOf(viewport);
    const model = createScaleModel({ extent, zoom: state.zoom, viewportWidth: width });
    const bar = controls.querySelector?.("[data-role='novegeo-map-scale-bar']");
    const label = controls.querySelector?.("[data-role='novegeo-map-scale-label']");
    if (bar?.style) bar.style.width = `${model.widthPx}px`;
    if (label) label.textContent = `≈ ${model.distanceKm} km`;
  };

  const renderEquator = (state) => {
    const { width, height } = rectOf(viewport);
    const padding = Math.min(36, Math.max(20, width * 0.055));
    const clampedY = calculateEquatorLabelY({ extent, height, padding, navigationState: state });
    Object.assign(equatorLabel.style || {}, { left: "8px", top: `${clampedY}px`, zIndex: "8" });
    equatorLabel.hidden = visibility.coordinates === false;
  };

  const renderSelection = (state) => {
    if (!selection) { marker.hidden = true; return; }
    const dims = rectOf(viewport);
    const padding = Math.min(36, Math.max(20, dims.width * 0.055));
    const point = coordinateToViewportPoint({ coordinate: selection.selectedCoordinate, extent, viewportWidth: dims.width, viewportHeight: dims.height, padding, navigationState: state });
    marker.hidden = point.x < 0 || point.x > dims.width || point.y < 0 || point.y > dims.height;
    Object.assign(marker.style || {}, { left: `${point.x}px`, top: `${point.y}px`, zIndex: "9" });
  };

  const controller = createMapNavigationController({ viewportElement: viewport, onChange: (state) => { renderScale(state); renderEquator(state); renderSelection(state); } });
  controller.apply();
  const bindings = bindMapNavigationInputs({ viewportElement: viewport, controller, windowRef });

  controls.querySelector?.("[data-map-action='zoom-in']")?.addEventListener?.("click", () => controller.zoomBy(1.25, "control"));
  controls.querySelector?.("[data-map-action='zoom-out']")?.addEventListener?.("click", () => controller.zoomBy(1 / 1.25, "control"));
  controls.querySelector?.("[data-map-action='reset']")?.addEventListener?.("click", () => controller.reset("control"));

  for (const input of controls.querySelectorAll?.("[data-layer-key]") || []) {
    input.addEventListener?.("change", () => {
      visibility = createLayerVisibility({ ...visibility, [input.dataset.layerKey]: input.checked });
      applyLayerVisibility(viewport, visibility);
      renderEquator(controller.state);
    });
  }

  const status = controls.querySelector?.("[data-role='novegeo-selection-status']");
  const form = controls.querySelector?.("[data-role='novegeo-coordinate-search']");
  form?.addEventListener?.("submit", (event) => {
    event.preventDefault?.();
    try {
      const longitude = form.elements?.longitude?.value;
      const latitude = form.elements?.latitude?.value;
      selection = resolveCoordinateSearch({ longitude, latitude, extent });
      if (status) status.textContent = `${selection.selectedCoordinate.latitude.toFixed(4)}°, ${selection.selectedCoordinate.longitude.toFixed(4)}°`;
      renderSelection(controller.state);
    } catch (error) {
      selection = null;
      renderSelection(controller.state);
      if (status) status.textContent = error instanceof Error ? error.message : String(error);
    }
  });

  viewport.addEventListener?.("click", (event) => {
    if (event.detail === 0) return;
    const rect = viewport.getBoundingClientRect?.() || { left: 0, top: 0, width: viewport.clientWidth, height: viewport.clientHeight };
    try {
      const padding = Math.min(36, Math.max(20, rect.width * 0.055));
      selection = viewportPointToCoordinate({ x: event.clientX - rect.left, y: event.clientY - rect.top, viewportWidth: rect.width, viewportHeight: rect.height, padding, extent, navigationState: controller.state });
      if (status) status.textContent = `${selection.selectedCoordinate.latitude.toFixed(4)}°, ${selection.selectedCoordinate.longitude.toFixed(4)}°`;
      renderSelection(controller.state);
    } catch { /* selection outside governed extent remains unchanged */ }
  });

  const deferredText = viewport.parentNode?.querySelector?.("p");
  if (deferredText?.textContent?.includes("Interaction, registry overlays and dynamic simulation remain deferred")) {
    deferredText.textContent = deferredText.textContent.replace("Interaction, registry overlays and dynamic simulation remain deferred.", "Map navigation and coordinate discovery are available. Registry overlays and dynamic simulation remain deferred.");
  }

  return Object.freeze({
    status: "READY",
    bundle: "12A",
    controller,
    get visibility() { return visibility; },
    get selection() { return selection; },
    disconnect() { bindings.disconnect(); },
  });
}
