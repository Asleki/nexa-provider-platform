/** P006.UI.6-P006.UI.9 — Additive authentication experience over the locked Bundle 12C shell. */
import { ApplicationRoute } from "../navigation/application-route.js";
import { createDevelopmentAuthClient } from "./development-auth-client.js";
import { createAuthenticationContext } from "./auth-context.js";
import { createAuthorizationContext } from "./authorization-context.js";
import { guestSignInMarkup } from "../../ui/pages/guest-sign-in.js";
import { developerSignInMarkup } from "../../ui/pages/developer-sign-in.js";
import { developerEnigmaMarkup } from "../../ui/pages/developer-enigma.js";
import { productionDeveloperWorkspaceMarkup } from "../../ui/pages/production-developer-workspace.js";
import { productionGuestWorkspaceMarkup } from "../../ui/pages/production-guest-workspace.js";
import { noveGeoFeatureMarkup } from "../../ui/pages/novegeo-feature.js";
import { resolveProductionWorkspace, WorkspaceKind } from "../workspaces/workspace-resolution.js";

const AUTH_ROUTES = new Set([
  ApplicationRoute.PRODUCTION_DEVELOPER,
  ApplicationRoute.PRODUCTION_GUEST,
  ApplicationRoute.PRODUCTION_NOVEGEO,
]);

function formValue(form, name) {
  return String(new FormData(form).get(name) || "").trim();
}

export function installAuthenticationExperience({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  application,
  client = createDevelopmentAuthClient({ windowRef }),
  context = createAuthenticationContext({ storage: windowRef?.sessionStorage }),
} = {}) {
  if (!documentRef?.querySelector) throw new TypeError("documentRef must provide querySelector");
  if (!application?.router) throw new TypeError("application router is required");
  const authorization = createAuthorizationContext(context);
  let pendingDeveloper = null;

  const outlet = () => documentRef.querySelector("[data-role='application-page']");

  const render = (route = application.route()) => {
    if (!AUTH_ROUTES.has(route)) return false;
    const target = outlet();
    if (!target) return false;
    if (context.authenticated) {
      const workspace = resolveProductionWorkspace(context.session);
      const root = documentRef.querySelector?.("#nexilabs-app");
      if (root) root.dataset.developerDiagnostics = String(workspace === WorkspaceKind.PRODUCTION_DEVELOPER);
      if (route === ApplicationRoute.PRODUCTION_NOVEGEO) {
        const backRoute = workspace === WorkspaceKind.PRODUCTION_DEVELOPER
          ? ApplicationRoute.PRODUCTION_DEVELOPER
          : ApplicationRoute.PRODUCTION_GUEST;
        target.innerHTML = noveGeoFeatureMarkup({ runtime: "production", backRoute });
        application.mountFeatureRuntime?.("production");
        return true;
      }
      if (workspace === WorkspaceKind.PRODUCTION_DEVELOPER) {
        target.innerHTML = productionDeveloperWorkspaceMarkup(context.session);
        return true;
      }
      if (workspace === WorkspaceKind.PRODUCTION_GUEST) {
        target.innerHTML = productionGuestWorkspaceMarkup(context.session);
        return true;
      }
      context.clear();
    }
    if (route === ApplicationRoute.PRODUCTION_NOVEGEO) {
      target.innerHTML = `<section class="entry-page" aria-labelledby="production-novegeo-access-title"><p class="eyebrow">Production</p><h1 id="production-novegeo-access-title">Authentication required</h1><p class="summary">Return to Production access and sign in before opening governed NoveGeo.</p><button class="text-button" type="button" data-route="${ApplicationRoute.PRODUCTION_ACCESS}">← Production access</button></section>`;
      return true;
    }
    if (route === ApplicationRoute.PRODUCTION_GUEST) {
      target.innerHTML = guestSignInMarkup();
      return true;
    }
    if (pendingDeveloper?.challenge) {
      target.innerHTML = developerEnigmaMarkup(pendingDeveloper.challenge);
      return true;
    }
    target.innerHTML = developerSignInMarkup();
    return true;
  };

  const showError = (markupFactory, error) => {
    const target = outlet();
    if (target) target.innerHTML = markupFactory({ error: error?.message || "Authentication failed." });
  };

  const onSubmit = async (event) => {
    const form = event.target?.closest?.("[data-auth-form]");
    if (!form) return;
    event.preventDefault();
    const route = application.route();
    try {
      if (form.dataset.authForm === "guest") {
        const payload = await client.loginGuest({
          username: formValue(form, "username"),
          password: formValue(form, "password"),
          runtime: application.selectedRuntime() || "production",
        });
        context.accept(payload.session);
        render(route);
        return;
      }
      if (form.dataset.authForm === "developer") {
        const payload = await client.startDeveloper({
          username: formValue(form, "username"),
          password: formValue(form, "password"),
          runtime: application.selectedRuntime() || "production",
        });
        pendingDeveloper = { attemptId: payload.attemptId, challenge: payload.challenge };
        render(route);
        return;
      }
      if (form.dataset.authForm === "developer-enigma") {
        const payload = await client.verifyDeveloper({
          attemptId: pendingDeveloper?.attemptId || "",
          response: formValue(form, "response"),
        });
        pendingDeveloper = null;
        context.accept(payload.session);
        render(route);
      }
    } catch (error) {
      if (form.dataset.authForm === "guest") showError(guestSignInMarkup, error);
      else if (form.dataset.authForm === "developer") showError(developerSignInMarkup, error);
      else {
        const target = outlet();
        if (target && pendingDeveloper?.challenge) {
          target.innerHTML = developerEnigmaMarkup(pendingDeveloper.challenge, { error: error?.message || "Enigma verification failed." });
        }
      }
    }
  };

  const onClick = async (event) => {
    const target = event.target?.closest?.("[data-auth-action]");
    if (!target) return;
    if (target.dataset.authAction === "logout") {
      const token = context.session?.sessionId;
      try {
        if (token) await client.logout(token);
      } catch {
        // Local context is still cleared even if the development authority is unavailable.
      }
      pendingDeveloper = null;
      context.clear();
      const root = documentRef.querySelector?.("#nexilabs-app");
      if (root) root.dataset.developerDiagnostics = "false";
      application.router.navigate(ApplicationRoute.RUNTIME_GATEWAY);
    }
  };

  const onHashChange = () => queueMicrotask(() => render(application.route()));

  const restore = async () => {
    const token = context.pendingSessionId;
    if (!token || context.authenticated) return context.session;
    try {
      const payload = await client.session(token);
      context.accept(payload.session);
      render(application.route());
      return context.session;
    } catch {
      context.clear();
      render(application.route());
      return null;
    }
  };

  documentRef.addEventListener?.("submit", onSubmit);
  documentRef.addEventListener?.("click", onClick);
  windowRef?.addEventListener?.("hashchange", onHashChange);
  render(application.route());
  void restore();

  return Object.freeze({
    context,
    authorization,
    render,
    restore,
    dispose() {
      documentRef.removeEventListener?.("submit", onSubmit);
      documentRef.removeEventListener?.("click", onClick);
      windowRef?.removeEventListener?.("hashchange", onHashChange);
    },
  });
}
