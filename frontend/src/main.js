/** Browser entry point for the NexiLabs PWA. */

import { createRuntimeConfig } from "./config/runtime-config.js";
import { mountNexiLabsShell } from "./app/shell/nexilabs-shell.js";
import { registerServiceWorker } from "./pwa/service-worker-registration.js";

function readPublicRuntimeInput(documentRef) {
  const root = documentRef.documentElement;
  return {
    applicationVersion: root.dataset.applicationVersion || "0.1.0",
    runtimeMode: root.dataset.runtimeMode || "development",
    environmentName: root.dataset.environmentName || "development",
    apiBaseUrl: root.dataset.apiBaseUrl || "",
    buildReference: root.dataset.buildReference || "local-development",
  };
}

export async function bootstrap(documentRef = globalThis.document, windowRef = globalThis.window, fetchRef = globalThis.fetch) {
  const config = createRuntimeConfig(readPublicRuntimeInput(documentRef));
  const application = await mountNexiLabsShell({ documentRef, windowRef, fetchRef, config });
  void registerServiceWorker({ documentRef, windowRef });
  return application;
}

if (typeof document !== "undefined") {
  void bootstrap(document, globalThis.window, globalThis.fetch).catch((error) => {
    console.error("[NexiLabs PWA] Application bootstrap failed.", error);
  });
}
