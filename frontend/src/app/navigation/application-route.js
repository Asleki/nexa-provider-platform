/** P006.UI.1/P006.UI.15 — Stable NexiLabs application-route contract. */
export const ApplicationRoute = Object.freeze({
  RUNTIME_GATEWAY: "runtime-gateway",
  PRODUCTION_ACCESS: "production-access",
  PRODUCTION_DEVELOPER: "production-developer",
  PRODUCTION_GUEST: "production-guest",
  SIMULATION_ENTRY: "simulation-entry",
  SIMULATION_NOVEGEO: "simulation-novegeo",
  PRODUCTION_NOVEGEO: "production-novegeo",
});

const ROUTE_HASH = Object.freeze({
  [ApplicationRoute.RUNTIME_GATEWAY]: "#/runtime",
  [ApplicationRoute.PRODUCTION_ACCESS]: "#/production",
  [ApplicationRoute.PRODUCTION_DEVELOPER]: "#/production/developer",
  [ApplicationRoute.PRODUCTION_GUEST]: "#/production/guest",
  [ApplicationRoute.SIMULATION_ENTRY]: "#/simulation",
  [ApplicationRoute.SIMULATION_NOVEGEO]: "#/simulation/novegeo",
  [ApplicationRoute.PRODUCTION_NOVEGEO]: "#/production/novegeo",
});

const HASH_ROUTE = Object.freeze(
  Object.fromEntries(Object.entries(ROUTE_HASH).map(([route, hash]) => [hash, route])),
);

export function isApplicationRoute(value) {
  return Object.values(ApplicationRoute).includes(value);
}

export function routeToHash(route) {
  if (!isApplicationRoute(route)) throw new Error(`Unsupported application route: ${route}`);
  return ROUTE_HASH[route];
}

export function routeFromHash(hash) {
  const normalized = String(hash || "").trim();
  return HASH_ROUTE[normalized] ?? ApplicationRoute.RUNTIME_GATEWAY;
}
