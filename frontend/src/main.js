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

  // Start the offline recovery boundary before shell partial loading. A slow/dead local
  // development server must not prevent the worker from being registered or updated.
  void registerServiceWorker({ documentRef, windowRef });

  const application = await mountNexiLabsShell({ documentRef, windowRef, fetchRef, config });
  void import("./app/auth/authentication-experience.js")
    .then(({ installAuthenticationExperience }) => installAuthenticationExperience({ documentRef, windowRef, application }))
    .catch((error) => console.warn("[NexiLabs PWA] Development authentication unavailable.", error));
  void import("./app/features/novegeo-national-geography-experience.js")
    .then(({ installNoveGeoNationalGeographyExperience }) => installNoveGeoNationalGeographyExperience({ documentRef, windowRef, fetchRef, apiBaseUrl: config.apiBaseUrl }))
    .catch((error) => console.warn("[NexiLabs PWA] Governed national geography unavailable.", error));
  void import("./app/features/novegeo-cartographic-styling-experience.js")
    .then(({ installNoveGeoCartographicStylingExperience }) => installNoveGeoCartographicStylingExperience({ documentRef, windowRef, fetchRef, apiBaseUrl: config.apiBaseUrl }))
    .catch((error) => console.warn("[NexiLabs PWA] Cartographic styling unavailable.", error));
  return application;
}

if (typeof document !== "undefined") {
  void bootstrap(document, globalThis.window, globalThis.fetch).catch((error) => {
    console.error("[NexiLabs PWA] Application bootstrap failed.", error);
  });
}
