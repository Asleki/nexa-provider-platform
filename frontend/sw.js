/** P003.2–P003.4 — Versioned offline application-shell service worker. */
const CACHE_NAME = "novegeo-shell-v6";
const OFFLINE_URL = "./index.html";
const APP_SHELL = [
  "./",
  "./index.html",
  "./public/manifest.webmanifest",
  "./public/brand/nexilabs/metadata/brand-tokens.css",
  "./public/brand/nexilabs/vectors/nexilabs_logo_horizontal.svg",
  "./public/brand/nexilabs/pwa/nexilabs_icon_192x192.png",
  "./public/brand/nexilabs/pwa/nexilabs_icon_512x512.png",
  "./styles/app.css",
  "./src/main.js",
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
  "./public/geography/novegeo/terrain/v001/manifest.json",
  "./public/geography/novegeo/terrain/v001/overview.json",
  "./public/geography/novegeo/terrain/v001/standard.json",
  "./public/geography/novegeo/landforms/v001/manifest.json",
  "./public/geography/novegeo/landforms/v001/standard.geojson"
];

self.addEventListener("install", (event) => {
  event.waitUntil(caches.open(CACHE_NAME).then((cache) => cache.addAll(APP_SHELL)));
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener("message", (event) => {
  if (event.data?.type === "SKIP_WAITING") self.skipWaiting();
});

self.addEventListener("fetch", (event) => {
  const request = event.request;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
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
