/** P006.UI.1-P006.UI.3/P006.UI.15 / Bundle 12.0C — NexiLabs-owned application shell. */
import { ApplicationState, ApplicationStatus } from "../../core/application-state.js";
import { applyBrand } from "../../branding/brand-config.js";
import { ApplicationRoute } from "../navigation/application-route.js";
import { createApplicationRouter } from "../navigation/application-router.js";
import { createRuntimeSelection } from "../navigation/runtime-selection.js";
import { loadShellPartials, shellPartialsReady } from "./partial-loader.js";
import { installShellPartialRecovery } from "./shell-recovery.js";
import { mountPrimaryNavigation } from "../../ui/navigation/primary-navigation.js";
import { runtimeGatewayMarkup } from "../../ui/pages/runtime-gateway.js";
import { productionAccessMarkup } from "../../ui/pages/production-access.js";
import { simulationWorkspaceMarkup } from "../../ui/pages/simulation-workspace.js";
import { noveGeoFeatureMarkup } from "../../ui/pages/novegeo-feature.js";
import { productionFeatureGuardMarkup } from "../../ui/pages/production-feature-guard.js";
import { accessPlaceholderMarkup } from "../../ui/pages/access-placeholder.js";
import { mountNoveGeoLiveAuthorityRuntime } from "../features/novegeo-live-authority-runtime.js";
import { mountNoveGeoMapShellHardeningRuntime } from "../features/novegeo-map-shell-hardening-runtime.js";

function pageMarkup(route) {
  switch (route) {
    case ApplicationRoute.PRODUCTION_ACCESS: return productionAccessMarkup();
    case ApplicationRoute.PRODUCTION_DEVELOPER: return accessPlaceholderMarkup("developer");
    case ApplicationRoute.PRODUCTION_GUEST: return accessPlaceholderMarkup("guest");
    case ApplicationRoute.SIMULATION_ENTRY: return simulationWorkspaceMarkup();
    case ApplicationRoute.SIMULATION_NOVEGEO: return noveGeoFeatureMarkup({ runtime: "simulation", backRoute: ApplicationRoute.SIMULATION_ENTRY });
    case ApplicationRoute.PRODUCTION_NOVEGEO: return productionFeatureGuardMarkup();
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

  // Shared chrome is important but must never be allowed to hold the entire PWA in BOOTING.
  try {
    await loadShellPartials({ documentRef, fetchRef });
    root.dataset.shellChromeStatus = "READY";
  } catch (error) {
    root.dataset.shellChromeStatus = "DEGRADED";
    root.dataset.shellChromeError = error?.name || "ShellPartialLoadError";
  }

  applyBrand(documentRef);

  const runtimeSelection = createRuntimeSelection();
  let router;
  let featureRuntime = null;
  let mapShellHardeningRuntime = null;

  const routeRuntime = (route) => {
    if (route === ApplicationRoute.SIMULATION_ENTRY || route === ApplicationRoute.SIMULATION_NOVEGEO) return "simulation";
    if ([ApplicationRoute.PRODUCTION_ACCESS, ApplicationRoute.PRODUCTION_DEVELOPER, ApplicationRoute.PRODUCTION_GUEST, ApplicationRoute.PRODUCTION_NOVEGEO].includes(route)) return "production";
    return null;
  };

  const renderRoute = (route) => {
    mapShellHardeningRuntime?.disconnect?.();
    mapShellHardeningRuntime = null;
    featureRuntime?.disconnect?.();
    featureRuntime = null;
    outlet.innerHTML = pageMarkup(route);
    root.dataset.applicationRoute = route;
    mountPrimaryNavigation(documentRef, route);
    const inferredRuntime = routeRuntime(route);
    if (inferredRuntime) runtimeSelection.select(inferredRuntime);
    else if (route === ApplicationRoute.RUNTIME_GATEWAY) runtimeSelection.clear();
    const selected = runtimeSelection.value;
    if (selected) root.dataset.selectedRuntime = selected;
    else delete root.dataset.selectedRuntime;
    root.dataset.developerDiagnostics = "false";
    if (route === ApplicationRoute.SIMULATION_NOVEGEO) {
      featureRuntime = mountNoveGeoLiveAuthorityRuntime({ documentRef, windowRef, fetchRef, apiBaseUrl: config.apiBaseUrl, runtimeMode: "simulation" });
      mapShellHardeningRuntime = mountNoveGeoMapShellHardeningRuntime({ documentRef, windowRef, authorityRuntime: featureRuntime });
    }
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
  const ready = state.transition(ApplicationStatus.READY, {
    reason: shellPartialsReady(documentRef) ? "nexilabs_shell_mounted" : "nexilabs_shell_mounted_degraded",
  });
  renderHealth(documentRef, root, config, ready);

  const recovery = installShellPartialRecovery({
    documentRef,
    windowRef,
    fetchRef,
    onRecovered() {
      root.dataset.shellChromeStatus = "READY";
      delete root.dataset.shellChromeError;
      applyBrand(documentRef);
      mountPrimaryNavigation(documentRef, router.route);
      renderHealth(documentRef, root, config, ready);
    },
  });

  return Object.freeze({
    applicationId: "nexilabs-pwa",
    applicationName: "NexiLabs PWA",
    status: ready.status,
    environmentName: config.environmentName,
    selectedRuntime: () => runtimeSelection.value,
    route: () => router.route,
    shellChromeReady: () => recovery.ready,
    recoverShellChrome: recovery.recover,
    mountFeatureRuntime(runtimeMode = runtimeSelection.value || "simulation") {
      featureRuntime?.disconnect?.();
      featureRuntime = mountNoveGeoLiveAuthorityRuntime({ documentRef, windowRef, fetchRef, apiBaseUrl: config.apiBaseUrl, runtimeMode });
      return featureRuntime;
    },
    router,
  });
}
