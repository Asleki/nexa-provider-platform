/** P006.UI.16 — Resolve and qualify the installed NexiLabs application boundary from the manifest URL. */

function requiredString(value, label) {
  const text = String(value ?? "").trim();
  if (!text) throw new TypeError(`${label} is required`);
  return text;
}

function normalizedDirectoryUrl(url) {
  const value = new URL(url);
  value.search = "";
  value.hash = "";
  if (!value.pathname.endsWith("/")) value.pathname = `${value.pathname}/`;
  return value;
}

export function expectedApplicationRootFromManifest(manifestUrl) {
  const manifest = new URL(requiredString(manifestUrl, "manifestUrl"));
  return normalizedDirectoryUrl(new URL("../", manifest));
}

export function resolveInstalledApplicationBoundary({ manifest, manifestUrl } = {}) {
  if (!manifest || typeof manifest !== "object" || Array.isArray(manifest)) {
    throw new TypeError("manifest must be an object");
  }
  const base = new URL(requiredString(manifestUrl, "manifestUrl"));
  const expectedRoot = expectedApplicationRootFromManifest(base);
  const idUrl = new URL(requiredString(manifest.id, "manifest.id"), base);
  const startUrl = new URL(requiredString(manifest.start_url, "manifest.start_url"), base);
  const scopeUrl = normalizedDirectoryUrl(new URL(requiredString(manifest.scope, "manifest.scope"), base));

  return Object.freeze({
    manifestUrl: base.href,
    expectedApplicationRoot: expectedRoot.href,
    idUrl: idUrl.href,
    startUrl: startUrl.href,
    scopeUrl: scopeUrl.href,
    startPathname: startUrl.pathname,
    startSearch: startUrl.search,
    startHash: startUrl.hash,
  });
}

export function urlWithinScope(url, scopeUrl) {
  const target = new URL(url);
  const scope = normalizedDirectoryUrl(scopeUrl);
  return target.origin === scope.origin && target.pathname.startsWith(scope.pathname);
}

export function inspectInstalledApplicationBoundary({ manifest, manifestUrl } = {}) {
  const resolved = resolveInstalledApplicationBoundary({ manifest, manifestUrl });
  const root = new URL(resolved.expectedApplicationRoot);
  const id = new URL(resolved.idUrl);
  const start = new URL(resolved.startUrl);
  const scope = new URL(resolved.scopeUrl);

  const applicationIdAtRoot = id.origin === root.origin && id.pathname === root.pathname && !id.search && !id.hash;
  const scopeAtRoot = scope.origin === root.origin && scope.pathname === root.pathname;
  const startAtRoot = start.origin === root.origin && start.pathname === root.pathname;
  const startInsideScope = urlWithinScope(start, scope);
  const sourceMarker = start.searchParams.get("source") === "pwa";
  const escapedIntoPublicDirectory = start.pathname.endsWith("/public/") || scope.pathname.endsWith("/public/");

  return Object.freeze({
    ...resolved,
    applicationIdAtRoot,
    scopeAtRoot,
    startAtRoot,
    startInsideScope,
    sourceMarker,
    escapedIntoPublicDirectory,
    passed: applicationIdAtRoot && scopeAtRoot && startAtRoot && startInsideScope && sourceMarker && !escapedIntoPublicDirectory,
  });
}

export function resolveBootstrapDependencies({ launchUrl } = {}) {
  const launch = new URL(requiredString(launchUrl, "launchUrl"));
  return Object.freeze({
    stylesheet: new URL("./styles/app.css", launch).href,
    mainModule: new URL("./src/main.js", launch).href,
    manifest: new URL("./public/manifest.webmanifest", launch).href,
    serviceWorker: new URL("./sw.js", launch).href,
  });
}
