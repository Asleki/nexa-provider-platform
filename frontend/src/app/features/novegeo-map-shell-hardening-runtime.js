/** P006.7.11.15.0 / Bundle 22A — compose additive map-shell hardening around the existing live authority runtime. */
import { mountNoveGeoMapShell } from "../../map/controls/novegeo-map-shell.js";

export function mountNoveGeoMapShellHardeningRuntime({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  authorityRuntime = null,
  mountShellRef = mountNoveGeoMapShell,
} = {}) {
  const shell = mountShellRef({ documentRef, windowRef });
  if (shell?.status !== "READY") {
    return Object.freeze({
      status: shell?.status || "UNAVAILABLE",
      reason: shell?.reason || "map_shell_unavailable",
      ready: Promise.resolve(Object.freeze({ status: shell?.status || "UNAVAILABLE" })),
      disconnect() { shell?.disconnect?.(); },
    });
  }

  let disconnected = false;
  const authorityReady = authorityRuntime?.ready && typeof authorityRuntime.ready.then === "function"
    ? authorityRuntime.ready
    : Promise.resolve(Object.freeze({ status: authorityRuntime?.status || "UNKNOWN" }));

  const ready = authorityReady.then((authorityReceipt) => {
    if (disconnected) return Object.freeze({ status: "DISCONNECTED" });
    const shellReceipt = shell.reconcile?.() || Object.freeze({ status: "READY" });
    return Object.freeze({
      status: shellReceipt.status === "READY" ? "READY" : "DEGRADED",
      authorityStatus: authorityReceipt?.status || authorityRuntime?.status || "UNKNOWN",
      shell: shellReceipt,
    });
  }).catch((error) => {
    if (disconnected) return Object.freeze({ status: "DISCONNECTED" });
    const shellReceipt = shell.reconcile?.() || Object.freeze({ status: "READY" });
    return Object.freeze({
      status: "DEGRADED",
      reason: "authority_completion_reconciliation_failed",
      error: error?.message || String(error),
      shell: shellReceipt,
    });
  });

  return Object.freeze({
    status: "READY",
    ready,
    shell,
    disconnect() {
      disconnected = true;
      shell.disconnect?.();
    },
  });
}
