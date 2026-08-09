/** P006.UI.1-P006.UI.3/P006.UI.15 — NexiLabs-owned application shell. */
import { ApplicationState, ApplicationStatus } from "../../core/application-state.js";
import { applyBrand } from "../../branding/brand-config.js";
import { ApplicationRoute } from "../navigation/application-route.js";
import { createApplicationRouter } from "../navigation/application-router.js";
import { createRuntimeSelection, SelectedRuntime } from "../navigation/runtime-selection.js";
import { loadShellPartials } from "./partial-loader.js";
import { mountPrimaryNavigation } from "../../ui/navigation/primary-navigation.js";
import { runtimeGatewayMarkup } from "../../ui/pages/runtime-gateway.js";
import { productionAccessMarkup } from "../../ui/pages/production-access.js";
import { simulationEntryMarkup } from "../../ui/pages/simulation-entry.js";
import { accessPlaceholderMarkup } from "../../ui/pages/access-placeholder.js";

function pageMarkup(route) {
  switch (route) {
    case ApplicationRoute.PRODUCTION_ACCESS: return productionAccessMarkup();
    case ApplicationRoute.PRODUCTION_DEVELOPER: return accessPlaceholderMarkup("developer");
    case ApplicationRoute.PRODUCTION_GUEST: return accessPlaceholderMarkup("guest");
    case ApplicationRoute.SIMULATION_ENTRY: return simulationEntryMarkup();
    case ApplicationRoute.RUNTIME_GATEWAY:
    default: return runtimeGatewayMarkup();
  }
}

function updateText(documentRef, selector, value) {
  for (const element of documentRef.querySelectorAll?.(selector) ?? []) element.textContent = value;
}

function renderHealth(documentRef, root, config, snapshot) {
  root.dataset.applicationStatus = snapshot.status;
  root.dataset.environmentName = config.environmentName;
  const label = snapshot.status === ApplicationStatus.READY ? "Ready" : snapshot.status.charAt(0) + snapshot.status.slice(1).toLowerCase();
  for (const element of documentRef.querySelectorAll?.("[data-role='application-status']") ?? []) {
    element.textContent = label;
    element.dataset.healthStatus = snapshot.status;
  }
  updateText(documentRef, "[data-role='environment-name']", config.environmentName);
  updateText(documentRef, "[data-role='application-version']", config.applicationVersion);
}

export async function mountNexiLabsShell({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  config,
  state = new ApplicationState(),
} = {}) {
  if (!documentRef?.querySelector) throw new TypeError("documentRef must provide querySelector");
  if (!config) throw new TypeError("config is required");
  const root = documentRef.querySelector("#nexilabs-app");
  const outlet = documentRef.querySelector("[data-role='application-page']");
  if (!root || !outlet) throw new Error("NexiLabs root shell is incomplete");

  state.transition(ApplicationStatus.BOOTING, { reason: "nexilabs_shell_start" });
  await loadShellPartials({ documentRef, fetchRef });
  applyBrand(documentRef);

  const runtimeSelection = createRuntimeSelection();
  let router;

  const renderRoute = (route) => {
    outlet.innerHTML = pageMarkup(route);
    root.dataset.applicationRoute = route;
    mountPrimaryNavigation(documentRef, route);
    const selected = runtimeSelection.value;
    if (selected) root.dataset.selectedRuntime = selected;
    else delete root.dataset.selectedRuntime;
    const main = documentRef.querySelector("#main-content");
    main?.focus?.({ preventScroll: true });
  };

  router = createApplicationRouter({ windowRef, onRoute: renderRoute });

  root.addEventListener?.("click", (event) => {
    const target = event.target?.closest?.("[data-route], [data-action], [data-select-runtime]");
    if (!target) return;
    if (target.dataset.selectRuntime) runtimeSelection.select(target.dataset.selectRuntime);
    if (target.dataset.action === "back") {
      event.preventDefault?.();
      router.back();
      return;
    }
    if (target.dataset.action === "toggle-navigation") {
      const navigation = documentRef.querySelector("[data-role='primary-navigation']");
      const open = navigation?.dataset.open !== "true";
      if (navigation) navigation.dataset.open = String(open);
      target.setAttribute?.("aria-expanded", String(open));
      return;
    }
    if (target.dataset.route) {
      event.preventDefault?.();
      router.navigate(target.dataset.route);
      const navigation = documentRef.querySelector("[data-role='primary-navigation']");
      const toggle = documentRef.querySelector("[data-action='toggle-navigation']");
      if (navigation) navigation.dataset.open = "false";
      toggle?.setAttribute?.("aria-expanded", "false");
    }
  });

  router.start();
  const ready = state.transition(ApplicationStatus.READY, { reason: "nexilabs_shell_mounted" });
  renderHealth(documentRef, root, config, ready);

  return Object.freeze({
    applicationId: "nexilabs-pwa",
    applicationName: "NexiLabs PWA",
    status: ready.status,
    environmentName: config.environmentName,
    selectedRuntime: () => runtimeSelection.value,
    route: () => router.route,
    router,
  });
}
