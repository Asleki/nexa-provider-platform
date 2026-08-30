/**
 * P006.7.11.15.9 compatibility maintenance — generic additive map-extension loader.
 *
 * The locked national/REGION/CITY experiences remain directly bootstrapped by main.js.
 * Later governed layers are registered through the append-only public manifest. The
 * loader fetches that manifest with a cache-busting query while online and retains the
 * last validated manifest in localStorage for offline re-entry. Imported module graphs
 * are cached by the existing service worker after their first successful online load.
 */

export const NOVEGEO_MAP_EXTENSION_MANIFEST_VERSION = 1;
export const NOVEGEO_MAP_EXTENSION_MANIFEST_URL = "./public/geography/novegeo/map-extensions/manifest.json";
export const NOVEGEO_MAP_EXTENSION_STORAGE_KEY = "nexilabs:novegeo-map-extensions:v1";

const EXTENSION_ID_PATTERN = /^nngla-map-extension:[a-z0-9][a-z0-9-]*:v[1-9][0-9]*$/;
const MODULE_PREFIX = "./src/app/features/novegeo-";
const MODULE_SUFFIX = "-map-experience.js";

export class NoveGeoMapExtensionManifestError extends Error {
  constructor(message, options = undefined) {
    super(message, options);
    this.name = "NoveGeoMapExtensionManifestError";
  }
}

function parseManifest(value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new NoveGeoMapExtensionManifestError("map extension manifest must be an object");
  }
  if (value.manifestVersion !== NOVEGEO_MAP_EXTENSION_MANIFEST_VERSION) {
    throw new NoveGeoMapExtensionManifestError("unsupported map extension manifest version");
  }
  if (!Array.isArray(value.extensions)) {
    throw new NoveGeoMapExtensionManifestError("map extension manifest extensions must be an array");
  }

  const seenIds = new Set();
  const seenModules = new Set();
  let previousOrder = -1;
  const extensions = value.extensions.map((entry) => {
    if (!entry || typeof entry !== "object" || Array.isArray(entry)) {
      throw new NoveGeoMapExtensionManifestError("map extension entry must be an object");
    }
    const keys = Object.keys(entry).sort();
    if (keys.join("|") !== "extensionId|module|order") {
      throw new NoveGeoMapExtensionManifestError("map extension entry requires extensionId, module and order only");
    }
    const extensionId = String(entry.extensionId ?? "");
    const module = String(entry.module ?? "");
    const order = entry.order;
    if (!EXTENSION_ID_PATTERN.test(extensionId)) {
      throw new NoveGeoMapExtensionManifestError(`invalid map extension id: ${extensionId}`);
    }
    if (!Number.isInteger(order) || order < 1 || order <= previousOrder) {
      throw new NoveGeoMapExtensionManifestError("map extension order must be strictly increasing positive integers");
    }
    if (!module.startsWith(MODULE_PREFIX) || !module.endsWith(MODULE_SUFFIX)) {
      throw new NoveGeoMapExtensionManifestError(`map extension module outside constrained feature namespace: ${module}`);
    }
    if (module.includes("..") || module.includes("?") || module.includes("#") || module.includes(":")) {
      throw new NoveGeoMapExtensionManifestError(`unsafe map extension module path: ${module}`);
    }
    if (seenIds.has(extensionId) || seenModules.has(module)) {
      throw new NoveGeoMapExtensionManifestError("duplicate map extension id or module");
    }
    seenIds.add(extensionId);
    seenModules.add(module);
    previousOrder = order;
    return Object.freeze({ extensionId, module, order });
  });
  return Object.freeze({
    manifestVersion: NOVEGEO_MAP_EXTENSION_MANIFEST_VERSION,
    extensions: Object.freeze(extensions),
  });
}

function storageOf(windowRef) {
  try {
    return windowRef?.localStorage || null;
  } catch {
    return null;
  }
}

function readStoredManifest(windowRef) {
  const storage = storageOf(windowRef);
  const raw = storage?.getItem?.(NOVEGEO_MAP_EXTENSION_STORAGE_KEY);
  if (!raw) return null;
  try {
    return parseManifest(JSON.parse(raw));
  } catch {
    storage?.removeItem?.(NOVEGEO_MAP_EXTENSION_STORAGE_KEY);
    return null;
  }
}

function storeManifest(windowRef, manifest) {
  const storage = storageOf(windowRef);
  try {
    storage?.setItem?.(NOVEGEO_MAP_EXTENSION_STORAGE_KEY, JSON.stringify(manifest));
  } catch {
    // Storage availability is not a publication authority. Online runtime can continue.
  }
}

export async function loadNoveGeoMapExtensionManifest({ fetchRef = globalThis.fetch, windowRef = globalThis.window } = {}) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef is required");
  const separator = NOVEGEO_MAP_EXTENSION_MANIFEST_URL.includes("?") ? "&" : "?";
  const freshUrl = `${NOVEGEO_MAP_EXTENSION_MANIFEST_URL}${separator}runtime=${Date.now()}`;
  try {
    const response = await fetchRef(freshUrl, { cache: "no-store" });
    if (!response?.ok) {
      throw new NoveGeoMapExtensionManifestError(`map extension manifest request failed with status ${response?.status ?? "unknown"}`);
    }
    const manifest = parseManifest(await response.json());
    storeManifest(windowRef, manifest);
    return Object.freeze({ manifest, source: "NETWORK" });
  } catch (error) {
    const stored = readStoredManifest(windowRef);
    if (stored) return Object.freeze({ manifest: stored, source: "LAST_VALIDATED_OFFLINE" });
    if (error instanceof NoveGeoMapExtensionManifestError) throw error;
    throw new NoveGeoMapExtensionManifestError("map extension manifest unavailable and no validated offline copy exists", { cause: error });
  }
}

function runtimeBaseUrl(windowRef, documentRef) {
  const base = documentRef?.baseURI || windowRef?.location?.href;
  if (!base) throw new NoveGeoMapExtensionManifestError("cannot resolve map extension module base URL");
  return new URL("./", base);
}

export async function installNoveGeoMapExtensions({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  apiBaseUrl = "",
  importModule = (specifier) => import(specifier),
} = {}) {
  if (typeof importModule !== "function") throw new TypeError("importModule is required");
  const { manifest, source } = await loadNoveGeoMapExtensionManifest({ fetchRef, windowRef });
  const baseUrl = runtimeBaseUrl(windowRef, documentRef);
  const receipts = [];

  for (const entry of manifest.extensions) {
    const moduleUrl = new URL(entry.module, baseUrl);
    if (moduleUrl.origin !== baseUrl.origin) {
      throw new NoveGeoMapExtensionManifestError(`cross-origin map extension module rejected: ${entry.extensionId}`);
    }
    const namespace = await importModule(moduleUrl.href);
    const install = namespace?.installNoveGeoMapExtension;
    if (typeof install !== "function") {
      throw new NoveGeoMapExtensionManifestError(`registered map extension does not export installNoveGeoMapExtension: ${entry.extensionId}`);
    }
    const receipt = await install({
      documentRef,
      windowRef,
      fetchRef,
      apiBaseUrl,
      extensionId: entry.extensionId,
    });
    receipts.push(Object.freeze({ extensionId: entry.extensionId, order: entry.order, receipt: receipt ?? null }));
  }

  return Object.freeze({
    status: "INSTALLED",
    manifestVersion: manifest.manifestVersion,
    manifestSource: source,
    extensionCount: receipts.length,
    receipts: Object.freeze(receipts),
  });
}

export { parseManifest as validateNoveGeoMapExtensionManifest };
