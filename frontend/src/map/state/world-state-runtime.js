/** P006.5 — browser presentation boundary for versioned world-state updates supplied by future NexiLabs sources. */
import { createWorldStateStore } from "./world-state-store.js";

export const WORLD_STATE_UPDATE_EVENT = "nexilabs:world-state-update";
const STATUS_ROLE = "novegeo-world-state-status";

function createStatusUi(documentRef, controls) {
  if (!controls || typeof documentRef?.createElement !== "function") return null;
  let node = controls.querySelector?.(`[data-role='${STATUS_ROLE}']`);
  if (node) return node;
  const wrapper = documentRef.createElement("div");
  wrapper.className = "map-state-status";
  wrapper.setAttribute("data-role", "novegeo-world-state");
  node = documentRef.createElement("span");
  node.setAttribute("data-role", STATUS_ROLE);
  node.setAttribute("aria-live", "polite");
  wrapper.append(node);
  controls.append(wrapper);
  return node;
}

function labelFor(state, receipt) {
  const count = state.stateReferences.length;
  if (receipt?.status && receipt.status !== "APPLIED" && receipt.status !== "DUPLICATE") {
    return `World state: ${receipt.status.toLowerCase().replaceAll("_", " ")} · rev ${state.revision}`;
  }
  return `World state: rev ${state.revision} · ${count} reference${count === 1 ? "" : "s"}`;
}

export function mountWorldStateRuntime({ documentRef, windowRef = globalThis.window, runtimeMode } = {}) {
  const controls = documentRef?.querySelector?.("[data-role='novegeo-map-discovery-controls']");
  if (!controls) return Object.freeze({ status: "UNAVAILABLE", reason: "map_controls_missing" });
  const statusNode = createStatusUi(documentRef, controls);
  const store = createWorldStateStore({ runtimeMode });
  let lastReceipt = Object.freeze({ status: "BASELINE", revision: 0, currentRevision: 0, reason: null });
  if (statusNode) statusNode.textContent = labelFor(store.state, lastReceipt);

  const applyUpdate = (update) => {
    lastReceipt = store.apply(update);
    if (statusNode) statusNode.textContent = labelFor(store.state, lastReceipt);
    return lastReceipt;
  };
  const onUpdate = (event) => applyUpdate(event?.detail);
  windowRef?.addEventListener?.(WORLD_STATE_UPDATE_EVENT, onUpdate);

  return Object.freeze({
    status: "READY",
    store,
    applyUpdate,
    get latestReceipt() { return lastReceipt; },
    disconnect() { windowRef?.removeEventListener?.(WORLD_STATE_UPDATE_EVENT, onUpdate); },
  });
}
