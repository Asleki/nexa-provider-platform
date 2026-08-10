/** P003.5 — Deterministic inspection of manifest, worker and cache-policy sources. */
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

export function readJson(path) { return JSON.parse(readFileSync(path, "utf8")); }
export function readText(path) { return readFileSync(path, "utf8"); }

function parseStringArray(source, constantName) {
  const match = source.match(new RegExp(`(?:const|export\\s+const)\\s+${constantName}\\s*=\\s*(?:Object\\.freeze\\()?\\s*\\[([\\s\\S]*?)\\]`));
  if (!match) throw new Error(`${constantName} array was not found`);
  return [...match[1].matchAll(/["']([^"']+)["']/g)].map((item) => item[1]);
}

function parseStringConstant(source, constantName) {
  const match = source.match(new RegExp(`(?:const|export\\s+const)\\s+${constantName}\\s*=\\s*["']([^"']+)["']`));
  if (!match) throw new Error(`${constantName} constant was not found`);
  return match[1];
}

export function inspectDeclaredPwaSources(frontendRoot) {
  const worker = readText(resolve(frontendRoot, "sw.js"));
  const policy = readText(resolve(frontendRoot, "src/pwa/cache-policy.js"));
  const registration = readText(resolve(frontendRoot, "src/pwa/service-worker-registration.js"));
  return Object.freeze({
    workerAssets: Object.freeze(parseStringArray(worker, "APP_SHELL")),
    policyAssets: Object.freeze(parseStringArray(policy, "APPLICATION_SHELL_ASSETS")),
    workerCacheVersion: parseStringConstant(worker, "CACHE_NAME"),
    policyCacheVersion: parseStringConstant(policy, "PWA_CACHE_VERSION"),
    workerOfflineDocument: parseStringConstant(worker, "OFFLINE_URL"),
    policyOfflineDocument: parseStringConstant(policy, "OFFLINE_DOCUMENT"),
    registrationUsesPolicyGeneration: /PWA_SHELL_GENERATION\s*=\s*PWA_CACHE_VERSION/.test(registration),
    workerSource: worker,
    policySource: policy,
    registrationSource: registration
  });
}

export function resolveLocalAsset(frontendRoot, relativeAsset) {
  if (!relativeAsset.startsWith("./")) throw new Error(`non-local asset: ${relativeAsset}`);
  const withoutPrefix = relativeAsset.slice(2);
  return resolve(frontendRoot, withoutPrefix || "index.html");
}
