/** P006.6 — integrated Bundle 12B state runtime above locked P004/P005 and Bundle 12A interaction. */
import { mountMapViewStateRuntime } from "./view-state-runtime.js";
import { mountWorldStateRuntime } from "./world-state-runtime.js";

export function mountP006StateIntegration({ documentRef, windowRef = globalThis.window, discovery, runtimeMode } = {}) {
  const viewState = mountMapViewStateRuntime({ documentRef, windowRef, discovery, runtimeMode });
  const worldState = mountWorldStateRuntime({ documentRef, windowRef, runtimeMode });
  const ready = viewState.status === "READY" && worldState.status === "READY";
  return Object.freeze({
    status: ready ? "READY" : "DEGRADED",
    bundle: "12B",
    viewState,
    worldState,
    disconnect() {
      viewState.disconnect?.();
      worldState.disconnect?.();
    },
  });
}
