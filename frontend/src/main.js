/** Browser entry point for the NexiLabs NoveGeo PWA. */

import { createApplication } from "./app/application.js";
import { createRuntimeConfig } from "./config/runtime-config.js";
import { registerServiceWorker } from "./pwa/service-worker-registration.js";
import { mountPhysicalLandPresentation } from "./map/environment/physical-land-presentation.js";
import { registerMapForegroundRecovery } from "./map/lifecycle/foreground-recovery.js";
import { mountFullViewportCoordinatePresentation } from "./map/environment/full-viewport-coordinate-presentation.js";
import { mountHydrologyAtmospherePresentation } from "./map/environment/hydrology-atmosphere-presentation.js";
import { mountBiospherePresentation } from "./map/environment/biosphere-presentation.js";
import { mountMapNavigationDiscovery } from "./map/interaction/map-navigation-discovery.js";

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

export function bootstrap(documentRef = globalThis.document, windowRef = globalThis.window) {
  const config = createRuntimeConfig(readPublicRuntimeInput(documentRef));
  const application = createApplication({ documentRef, config }).start();
  mountPhysicalLandPresentation(documentRef);
  mountBiospherePresentation(documentRef);
  mountHydrologyAtmospherePresentation(documentRef);
  mountFullViewportCoordinatePresentation(documentRef);
  mountMapNavigationDiscovery(documentRef, windowRef);
  registerMapForegroundRecovery({
    documentRef,
    windowRef,
    redrawMap: () => application.mapPresentation?.redraw?.() ?? { status: "UNAVAILABLE" },
    redrawPhysicalLand: () => {
      const physicalLand = mountPhysicalLandPresentation(documentRef);
      mountBiospherePresentation(documentRef);
      mountHydrologyAtmospherePresentation(documentRef);
      mountFullViewportCoordinatePresentation(documentRef);
      return physicalLand;
    },
  });
  void registerServiceWorker({ documentRef });
  return application;
}

if (typeof document !== "undefined") {
  try {
    bootstrap(document, globalThis.window);
  } catch (error) {
    console.error("[NexiLabs PWA] Application bootstrap failed.", error);
  }
}
