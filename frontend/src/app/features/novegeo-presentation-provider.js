/**
 * P006.7.11.15.10 — narrow additive provider seam for the core presentation coordinator.
 *
 * The shell installs the coordinator before any NoveGeo geographic renderer can run.
 * Governed layer adapters resolve that coordinator lazily. If no coordinator has been
 * installed (for example in legacy/unit contexts), the adapters retain their historical
 * renderer behavior unchanged.
 */
import { createNoveGeoPresentationCoordinator } from "../../map/cartography/presentation-coordinator.js";

let activeCoordinator = null;

export function installNoveGeoPresentationCoordinator({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  createCoordinatorRef = createNoveGeoPresentationCoordinator,
} = {}) {
  if (activeCoordinator) return activeCoordinator;
  activeCoordinator = createCoordinatorRef({ documentRef, windowRef });
  return activeCoordinator;
}

export function getNoveGeoPresentationCoordinator() {
  return activeCoordinator;
}

export function resolveNoveGeoPresentationCoordinator(explicitCoordinator = undefined) {
  return explicitCoordinator === undefined ? activeCoordinator : explicitCoordinator;
}

export function registerNoveGeoPresentationSnapshot(presentationCoordinator, {
  layerKey,
  items,
  candidates,
  readRuntime = null,
  semanticChecksum = null,
} = {}) {
  if (!presentationCoordinator || typeof presentationCoordinator.registerLayerSnapshot !== "function") {
    return Object.freeze({ status: "LEGACY_ONLY", activePresentationMode: "LEGACY" });
  }
  return presentationCoordinator.registerLayerSnapshot({
    layerKey,
    items,
    candidates,
    readRuntime,
    semanticChecksum,
  });
}

export function unifiedPresentationOwnsLayer(presentationCoordinator) {
  return presentationCoordinator?.mode === "UNIFIED";
}

export function resetNoveGeoPresentationCoordinatorForTests() {
  activeCoordinator?.disconnect?.();
  activeCoordinator = null;
}
