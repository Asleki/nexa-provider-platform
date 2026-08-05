/** P003.3/P003.4 — Immutable application-shell cache policy. */
export const PWA_CACHE_VERSION = "novegeo-shell-v1";
export const OFFLINE_DOCUMENT = "./index.html";
export const APPLICATION_SHELL_ASSETS = Object.freeze([
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
  "./src/pwa/service-worker-registration.js"
]);

export function isCurrentApplicationCache(cacheName) {
  return cacheName === PWA_CACHE_VERSION;
}
