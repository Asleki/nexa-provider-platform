/** Browser entry point for the NexiLabs NoveGeo PWA. */

import { createApplication } from "./app/application.js";
import { createRuntimeConfig } from "./config/runtime-config.js";

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
  return createApplication({ documentRef, config }).start();
}

if (typeof document !== "undefined") {
  try {
    bootstrap(document);
  } catch (error) {
    console.error("[NexiLabs PWA] Application bootstrap failed.", error);
  }
}
