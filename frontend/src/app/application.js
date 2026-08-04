/**
 * NexiLabs NoveGeo PWA
 * P002.1/P002.2 — Deterministic application bootstrap.
 */

import { ApplicationState, ApplicationStatus } from "../core/application-state.js";

function requireElement(documentRef, selector) {
  const element = documentRef.querySelector(selector);
  if (!element) throw new Error(`Required application element not found: ${selector}`);
  return element;
}

function renderHealth({ root, statusElement, config, snapshot }) {
  root.dataset.applicationStatus = snapshot.status;
  root.dataset.runtimeMode = config.runtimeMode;
  statusElement.dataset.healthStatus = snapshot.status;
  statusElement.textContent = snapshot.status === ApplicationStatus.READY
    ? "Ready"
    : snapshot.status.charAt(0) + snapshot.status.slice(1).toLowerCase();
}

export function createApplication({
  documentRef = globalThis.document,
  config,
  state = new ApplicationState(),
  clock = () => new Date().toISOString(),
} = {}) {
  if (!documentRef || typeof documentRef.querySelector !== "function") {
    throw new TypeError("documentRef must provide querySelector");
  }
  if (!config || typeof config !== "object") {
    throw new TypeError("config is required");
  }
  if (!(state instanceof ApplicationState)) {
    throw new TypeError("state must be an ApplicationState");
  }
  if (typeof clock !== "function") {
    throw new TypeError("clock must be a function");
  }

  let startReceipt = null;

  return Object.freeze({
    get state() {
      return state.snapshot;
    },

    start() {
      if (startReceipt) return startReceipt;
      state.transition(ApplicationStatus.BOOTING, { reason: "application_start" });

      try {
        const root = requireElement(documentRef, "#nexilabs-app");
        const statusElement = requireElement(documentRef, "[data-role='application-status']");
        const runtimeElement = requireElement(documentRef, "[data-role='runtime-mode']");
        const versionElement = requireElement(documentRef, "[data-role='application-version']");

        runtimeElement.textContent = config.runtimeMode;
        versionElement.textContent = config.applicationVersion;
        const readySnapshot = state.transition(ApplicationStatus.READY, {
          reason: "application_mounted",
        });
        renderHealth({ root, statusElement, config, snapshot: readySnapshot });

        startReceipt = Object.freeze({
          applicationId: config.applicationId,
          applicationName: config.applicationName,
          applicationVersion: config.applicationVersion,
          runtimeMode: config.runtimeMode,
          status: readySnapshot.status,
          startedAt: readySnapshot.changedAt,
          readyAt: clock(),
          capabilities: config.capabilities,
        });
        return startReceipt;
      } catch (error) {
        const failedSnapshot = state.transition(ApplicationStatus.FAILED, {
          reason: "bootstrap_failure",
          message: error instanceof Error ? error.message : String(error),
        });
        const root = documentRef.querySelector("#nexilabs-app");
        const statusElement = documentRef.querySelector("[data-role='application-status']");
        if (root && statusElement) {
          renderHealth({ root, statusElement, config, snapshot: failedSnapshot });
        }
        throw error;
      }
    },
  });
}
