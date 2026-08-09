/** P006.UI.15 — Primary NexiLabs navigation with explicit planned placeholders. */
import { ApplicationRoute, routeToHash } from "../../app/navigation/application-route.js";

export function primaryNavigationItems() {
  return Object.freeze([
    Object.freeze({ label: "Home", route: ApplicationRoute.RUNTIME_GATEWAY, available: true }),
    Object.freeze({ label: "Simulation", route: ApplicationRoute.SIMULATION_ENTRY, available: true }),
    Object.freeze({ label: "Production", route: ApplicationRoute.PRODUCTION_ACCESS, available: true }),
    Object.freeze({ label: "NoveGeo", available: false, status: "Planned" }),
    Object.freeze({ label: "Registries", available: false, status: "Planned" }),
  ]);
}

export function navigationMarkup(activeRoute) {
  return primaryNavigationItems().map((item) => {
    if (!item.available) {
      return `<span class="nav-item nav-item-planned" aria-disabled="true">${item.label}<small>${item.status}</small></span>`;
    }
    const current = item.route === activeRoute ? ' aria-current="page"' : "";
    return `<a class="nav-item" href="${routeToHash(item.route)}" data-route="${item.route}"${current}>${item.label}</a>`;
  }).join("");
}

export function mountPrimaryNavigation(documentRef, activeRoute) {
  const navigation = documentRef?.querySelector?.("[data-role='primary-navigation']");
  if (!navigation) return Object.freeze({ mounted: false, itemCount: 0 });
  const items = primaryNavigationItems();
  navigation.innerHTML = navigationMarkup(activeRoute);
  return Object.freeze({ mounted: true, itemCount: items.length });
}
