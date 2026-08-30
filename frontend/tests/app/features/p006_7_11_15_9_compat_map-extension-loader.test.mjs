import test from "node:test";
import assert from "node:assert/strict";
import {
  NOVEGEO_MAP_EXTENSION_MANIFEST_URL,
  NOVEGEO_MAP_EXTENSION_STORAGE_KEY,
  NoveGeoMapExtensionManifestError,
  installNoveGeoMapExtensions,
  loadNoveGeoMapExtensionManifest,
  validateNoveGeoMapExtensionManifest,
} from "../../../src/app/features/novegeo-map-extension-loader.js";

function storageHarness() {
  const values = new Map();
  return {
    getItem(key) { return values.has(key) ? values.get(key) : null; },
    setItem(key, value) { values.set(key, String(value)); },
    removeItem(key) { values.delete(key); },
    values,
  };
}

const municipality = Object.freeze({
  extensionId: "nngla-map-extension:municipality:v1",
  order: 100,
  module: "./src/app/features/novegeo-municipality-map-experience.js",
});
const district = Object.freeze({
  extensionId: "nngla-map-extension:city-district:v1",
  order: 200,
  module: "./src/app/features/novegeo-city-district-map-experience.js",
});


test("empty manifest is a valid identity extension set", () => {
  const manifest = validateNoveGeoMapExtensionManifest({ manifestVersion: 1, extensions: [] });
  assert.equal(manifest.manifestVersion, 1);
  assert.equal(manifest.extensions.length, 0);
});


test("manifest validation is ordered, duplicate-safe and namespace constrained", () => {
  assert.equal(validateNoveGeoMapExtensionManifest({ manifestVersion: 1, extensions: [municipality, district] }).extensions.length, 2);
  assert.throws(
    () => validateNoveGeoMapExtensionManifest({ manifestVersion: 1, extensions: [district, municipality] }),
    NoveGeoMapExtensionManifestError,
  );
  assert.throws(
    () => validateNoveGeoMapExtensionManifest({
      manifestVersion: 1,
      extensions: [{ extensionId: "nngla-map-extension:x:v1", order: 100, module: "https://evil.example/x.js" }],
    }),
    NoveGeoMapExtensionManifestError,
  );
});


test("online manifest is cache-busted, validated and retained for offline re-entry", async () => {
  const localStorage = storageHarness();
  const windowRef = { localStorage, location: { href: "https://novegeo.example/" } };
  const calls = [];
  const fetchRef = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, status: 200, async json() { return { manifestVersion: 1, extensions: [municipality] }; } };
  };
  const online = await loadNoveGeoMapExtensionManifest({ fetchRef, windowRef });
  assert.equal(online.source, "NETWORK");
  assert.equal(online.manifest.extensions.length, 1);
  assert.match(calls[0].url, new RegExp(`^${NOVEGEO_MAP_EXTENSION_MANIFEST_URL.replaceAll(".", "\\.")}\\?runtime=\\d+$`));
  assert.equal(calls[0].options.cache, "no-store");
  assert.ok(localStorage.values.has(NOVEGEO_MAP_EXTENSION_STORAGE_KEY));

  const offline = await loadNoveGeoMapExtensionManifest({
    fetchRef: async () => { throw new Error("offline"); },
    windowRef,
  });
  assert.equal(offline.source, "LAST_VALIDATED_OFFLINE");
  assert.equal(offline.manifest.extensions[0].extensionId, municipality.extensionId);
});


test("registered extensions install sequentially after same-origin URL resolution", async () => {
  const localStorage = storageHarness();
  const windowRef = { localStorage, location: { href: "https://novegeo.example/app/" } };
  const documentRef = { baseURI: "https://novegeo.example/app/" };
  const imported = [];
  const installed = [];
  const fetchRef = async () => ({
    ok: true,
    status: 200,
    async json() { return { manifestVersion: 1, extensions: [municipality, district] }; },
  });
  const importModule = async (specifier) => {
    imported.push(specifier);
    return {
      async installNoveGeoMapExtension(input) {
        installed.push(input.extensionId);
        return { status: "RENDERED" };
      },
    };
  };

  const receipt = await installNoveGeoMapExtensions({
    documentRef,
    windowRef,
    fetchRef,
    apiBaseUrl: "/api/v1",
    importModule,
  });
  assert.equal(receipt.status, "INSTALLED");
  assert.equal(receipt.extensionCount, 2);
  assert.deepEqual(installed, [municipality.extensionId, district.extensionId]);
  assert.deepEqual(imported, [
    "https://novegeo.example/app/src/app/features/novegeo-municipality-map-experience.js",
    "https://novegeo.example/app/src/app/features/novegeo-city-district-map-experience.js",
  ]);
});
