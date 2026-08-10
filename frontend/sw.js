/** P003.2–P003.4 — Versioned offline application-shell service worker. */
const CACHE_NAME = "nexilabs-shell-v16";
const OFFLINE_URL = "./index.html";
const NAVIGATION_NETWORK_TIMEOUT_MS = 1800;
const APP_SHELL = [
  "./",
  "./index.html",
  "./public/manifest.webmanifest",
  "./public/brand/nexilabs/metadata/brand-tokens.css",
  "./public/brand/nexilabs/vectors/nexilabs_logo_horizontal.svg",
  "./public/brand/nexilabs/pwa/nexilabs_icon_192x192.png",
  "./public/brand/nexilabs/pwa/nexilabs_icon_512x512.png",
  "./public/brand/nexilabs/pwa/nexilabs_maskable_192x192.png",
  "./public/brand/nexilabs/pwa/nexilabs_maskable_512x512.png",
  "./styles/app.css",
  "./src/main.js",
  "./src/ui/partials/header.html",
  "./src/ui/partials/footer.html",
  "./src/app/navigation/application-route.js",
  "./src/app/navigation/application-router.js",
  "./src/app/navigation/runtime-selection.js",
  "./src/app/shell/partial-loader.js",
  "./src/app/shell/shell-recovery.js",
  "./src/app/shell/nexilabs-shell.js",
  "./src/ui/navigation/primary-navigation.js",
  "./src/ui/pages/runtime-gateway.js",
  "./src/ui/pages/production-access.js",
  "./src/ui/pages/simulation-entry.js",
  "./src/ui/pages/access-placeholder.js",
  "./src/ui/pages/simulation-workspace.js",
  "./src/ui/pages/novegeo-feature.js",
  "./src/ui/pages/production-feature-guard.js",
  "./src/app/workspaces/workspace-capabilities.js",
  "./src/app/features/novegeo-feature-runtime.js",
  "./src/app/features/novegeo-feature-geometry.js",
  "./src/app/application.js",
  "./src/branding/brand-assets.js",
  "./src/branding/brand-config.js",
  "./src/config/runtime-config.js",
  "./src/core/application-state.js",
  "./src/pwa/cache-policy.js",
  "./src/pwa/service-worker-registration.js",
  "./src/map/geography/contracts.js",
  "./src/map/geography/projection.js",
  "./src/map/geography/status.js",
  "./src/map/presentation/boundary-render-plan.js",
  "./src/map/presentation/canvas-renderer.js",
  "./src/map/presentation/contracts.js",
  "./src/map/presentation/coordinate-grid.js",
  "./src/map/presentation/coordinate-labels.js",
  "./src/map/presentation/index.js",
  "./src/map/presentation/map-presentation.js",
  "./src/map/presentation/publication.js",
  "./src/map/presentation/viewport.js",
  "./src/map/publication/contracts.js",
  "./src/map/publication/catalog.js",
  "./src/map/publication/index.js",
  "./src/map/publication/v002-overview.js",
  "./src/map/publication/v002-standard.js",
  "./public/geography/novegeo/world-boundary/v002/manifest.json",
  "./public/geography/novegeo/world-boundary/v002/overview.geojson",
  "./public/geography/novegeo/world-boundary/v002/standard.geojson",
  "./src/map/validation/contracts.js",
  "./src/map/validation/geometry-validator.js",
  "./src/map/validation/extent-calculator.js",
  "./src/map/validation/extent-validator.js",
  "./src/map/validation/projection-validator.js",
  "./src/map/validation/viewport-validator.js",
  "./src/map/validation/qualification.js",
  "./src/map/validation/index.js",
  "./src/map/terrain/contracts.js",
  "./src/map/terrain/catalog.js",
  "./src/map/terrain/render-plan.js",
  "./src/map/landforms/contracts.js",
  "./src/map/landforms/catalog.js",
  "./src/map/landforms/render-plan.js",
  "./src/map/environment/physical-land-presentation.js",
  "./src/map/environment/full-viewport-coordinate-presentation.js",
  "./src/map/lifecycle/foreground-recovery.js",
  "./src/map/hydrology/contracts.js",
  "./src/map/hydrology/catalog.js",
  "./src/map/hydrology/render-plan.js",
  "./src/map/climate/contracts.js",
  "./src/map/climate/catalog.js",
  "./src/map/climate/render-plan.js",
  "./src/map/environment/hydrology-atmosphere-presentation.js",
  "./src/map/vegetation/contracts.js",
  "./src/map/vegetation/catalog.js",
  "./src/map/vegetation/render-plan.js",
  "./src/map/environment/biosphere-presentation.js",
  "./src/map/interaction/navigation-state.js",
  "./src/map/interaction/navigation-controller.js",
  "./src/map/interaction/input-bindings.js",
  "./src/map/interaction/map-navigation-discovery.js",
  "./src/map/controls/layer-state.js",
  "./src/map/controls/scale.js",
  "./src/map/selection/coordinate-search.js",
  "./src/map/selection/location-selection.js",
  "./src/map/state/view-state-contracts.js",
  "./src/map/state/view-state-storage.js",
  "./src/map/state/view-state-runtime.js",
  "./src/map/state/world-state-contracts.js",
  "./src/map/state/world-state-store.js",
  "./src/map/state/world-state-runtime.js",
  "./src/map/state/p006-state-integration.js",
  "./public/geography/novegeo/vegetation/v001/manifest.json",
  "./public/geography/novegeo/vegetation/v001/standard.json",
  "./public/geography/novegeo/hydrology/v001/manifest.json",
  "./public/geography/novegeo/hydrology/v001/standard.json",
  "./public/geography/novegeo/climate/v001/manifest.json",
  "./public/geography/novegeo/climate/v001/standard.json",
  "./public/geography/novegeo/terrain/v001/manifest.json",
  "./public/geography/novegeo/terrain/v001/overview.json",
  "./public/geography/novegeo/terrain/v001/standard.json",
  "./public/geography/novegeo/landforms/v001/manifest.json",
  "./public/geography/novegeo/landforms/v001/standard.geojson"
];

self.addEventListener("install", (event) => {
  event.waitUntil((async () => {
    const cache = await caches.open(CACHE_NAME);
    await cache.addAll(APP_SHELL);
    // Bundle 12.0E: activate only after the complete replacement shell is cached.
    await self.skipWaiting();
  })());
});

self.addEventListener("activate", (event) => {
  event.waitUntil((async () => {
    const keys = await caches.keys();
    const previousShellKeys = keys.filter((key) => key.startsWith("nexilabs-shell-") && key !== CACHE_NAME);
    await Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key)));
    await self.clients.claim();

    // A previously controlled page can keep its old ES-module graph in memory even after
    // controllerchange. Navigate stale window clients exactly once per shell generation so
    // they restart against the newly completed cache. First installation has no old shell
    // cache and therefore does not cause an unnecessary reload.
    if (previousShellKeys.length > 0) {
      const clients = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
      await Promise.all(clients.map((client) => {
        if (!client.url?.startsWith(self.location.origin)) return undefined;
        return client.navigate(client.url);
      }));
    }
  })());
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

async function navigationResponse(request) {
  const controller = typeof AbortController === "function" ? new AbortController() : null;
  let timer;
  try {
    if (controller) timer = setTimeout(() => controller.abort(), NAVIGATION_NETWORK_TIMEOUT_MS);
    return await fetch(request, controller ? { signal: controller.signal } : undefined);
  } catch {
    return (await caches.match(request)) || caches.match(OFFLINE_URL);
  } finally {
    if (timer) clearTimeout(timer);
  }
}

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(navigationResponse(request));
    return;
  }

  event.respondWith(
    caches.match(request).then((cached) => cached || fetch(request).then((response) => {
      if (!response || response.status !== 200 || response.type === "opaque") return response;
      const copy = response.clone();
      caches.open(CACHE_NAME).then((cache) => cache.put(request, copy));
      return response;
    }))
  );
});
