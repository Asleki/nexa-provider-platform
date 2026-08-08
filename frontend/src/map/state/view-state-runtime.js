/** P006.4 — recover and persist Bundle 12A navigation, layers and selection without creating registry authority. */
import { createMapViewState } from "./view-state-contracts.js";
import { createMapViewStateRepository } from "./view-state-storage.js";

const STATUS_ROLE = "novegeo-view-state-status";
const CLEAR_ROLE = "novegeo-clear-saved-view";

function eventCtor(windowRef) {
  return windowRef?.Event ?? globalThis.Event;
}

function dispatch(node, type, windowRef) {
  if (!node?.dispatchEvent) return false;
  const EventCtor = eventCtor(windowRef);
  if (typeof EventCtor !== "function") return false;
  node.dispatchEvent(new EventCtor(type, { bubbles: true, cancelable: true }));
  return true;
}

function setStatus(controls, text) {
  const node = controls?.querySelector?.(`[data-role='${STATUS_ROLE}']`);
  if (node) node.textContent = text;
}

function restoreNavigation(controller, navigation) {
  controller.reset?.("view-state-recovery");
  if (Number(navigation.zoom) !== 1) controller.zoomTo?.(navigation.zoom, "view-state-recovery");
  if (Number(navigation.offsetX) !== 0 || Number(navigation.offsetY) !== 0) {
    controller.panBy?.(navigation.offsetX, navigation.offsetY, "view-state-recovery");
  }
}

export function captureMapViewState({ discovery, runtimeMode, revision = 0 } = {}) {
  if (!discovery?.controller) throw new TypeError("Bundle 12A discovery controller is required");
  return createMapViewState({
    revision,
    runtimeMode,
    navigation: discovery.controller.state,
    layerVisibility: discovery.visibility,
    selection: discovery.selection,
  });
}

export function restoreMapViewState({ state, discovery, controls, windowRef } = {}) {
  if (!state || !discovery?.controller) throw new TypeError("state and Bundle 12A discovery controller are required");
  restoreNavigation(discovery.controller, state.navigation);

  for (const input of controls?.querySelectorAll?.("[data-layer-key]") || []) {
    const next = state.layerVisibility?.[input.dataset.layerKey] !== false;
    if (input.checked !== next) {
      input.checked = next;
      dispatch(input, "change", windowRef);
    }
  }

  if (state.selection) {
    const form = controls?.querySelector?.("[data-role='novegeo-coordinate-search']");
    if (form?.elements?.longitude && form?.elements?.latitude) {
      form.elements.longitude.value = String(state.selection.longitude);
      form.elements.latitude.value = String(state.selection.latitude);
      dispatch(form, "submit", windowRef);
    }
  }
  return Object.freeze({ status: "RESTORED", revision: state.revision });
}

function createStatusUi(documentRef, controls) {
  if (!controls || typeof documentRef?.createElement !== "function") return;
  if (controls.querySelector?.(`[data-role='${STATUS_ROLE}']`)) return;
  const wrapper = documentRef.createElement("div");
  wrapper.className = "map-state-status";
  wrapper.setAttribute("data-role", "novegeo-map-view-state");
  const status = documentRef.createElement("span");
  status.setAttribute("data-role", STATUS_ROLE);
  status.setAttribute("aria-live", "polite");
  status.textContent = "View state: session only";
  const clear = documentRef.createElement("button");
  clear.type = "button";
  clear.setAttribute("data-role", CLEAR_ROLE);
  clear.textContent = "Forget saved view";
  wrapper.append(status, clear);
  controls.append(wrapper);
}

export function mountMapViewStateRuntime({ documentRef, windowRef = globalThis.window, discovery, runtimeMode } = {}) {
  const viewport = documentRef?.querySelector?.("[data-role='future-map-viewport']");
  const controls = documentRef?.querySelector?.("[data-role='novegeo-map-discovery-controls']");
  if (!viewport || !controls || !discovery?.controller) return Object.freeze({ status: "UNAVAILABLE", reason: "bundle_12a_unavailable" });

  createStatusUi(documentRef, controls);
  const repository = createMapViewStateRepository({ storage: windowRef?.localStorage, runtimeMode });
  let persistenceRevision = 0;
  let lastReceipt = repository.load();

  if (lastReceipt.status === "RESTORED") {
    persistenceRevision = lastReceipt.state.revision;
    restoreMapViewState({ state: lastReceipt.state, discovery, controls, windowRef });
    setStatus(controls, `View state: restored · rev ${persistenceRevision}`);
  } else if (lastReceipt.status === "REJECTED") {
    setStatus(controls, "View state: incompatible saved state cleared");
  } else if (repository.available) {
    setStatus(controls, "View state: ready to save locally");
  }

  const persist = () => {
    if (!repository.available) return Object.freeze({ status: "UNAVAILABLE" });
    persistenceRevision += 1;
    const state = captureMapViewState({ discovery, runtimeMode, revision: persistenceRevision });
    lastReceipt = repository.save(state);
    setStatus(controls, `View state: saved locally · rev ${persistenceRevision}`);
    return lastReceipt;
  };

  const listeners = [];
  const on = (target, type, handler, options) => {
    target?.addEventListener?.(type, handler, options);
    listeners.push(() => target?.removeEventListener?.(type, handler, options));
  };
  for (const type of ["pointerup", "touchend", "wheel", "keyup", "click"]) on(viewport, type, persist);
  for (const type of ["change", "submit", "click"]) on(controls, type, persist);
  on(windowRef, "pagehide", persist);
  on(documentRef, "visibilitychange", () => { if (documentRef.hidden === true) persist(); });

  controls.querySelector?.(`[data-role='${CLEAR_ROLE}']`)?.addEventListener?.("click", () => {
    lastReceipt = repository.clear();
    persistenceRevision = 0;
    setStatus(controls, "View state: saved view forgotten");
  });

  return Object.freeze({
    status: "READY",
    repository,
    persist,
    get latestReceipt() { return lastReceipt; },
    disconnect() { for (const dispose of listeners) dispose(); },
  });
}
