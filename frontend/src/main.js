/** Browser entry point for the NexiLabs NoveGeo PWA. */

import { createApplication } from "./app/application.js";
import { createRuntimeConfig } from "./config/runtime-config.js";
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

export function bootstrap(documentRef = globalThis.document) {
  const config = createRuntimeConfig(readPublicRuntimeInput(documentRef));
  const application = createApplication({ documentRef, config }).start();
  void registerServiceWorker({ documentRef });
  return application;
}

if (typeof document !== "undefined") {
  try {
    bootstrap(document);
  } catch (error) {
    console.error("[NexiLabs PWA] Application bootstrap failed.", error);
  }
}
