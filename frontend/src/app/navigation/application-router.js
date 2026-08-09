/** P006.UI.1/P006.UI.15 — Hash-based application navigation, separate from map navigation. */
import { ApplicationRoute, routeFromHash, routeToHash } from "./application-route.js";

export function createApplicationRouter({ windowRef = globalThis.window, onRoute = () => {} } = {}) {
  if (typeof onRoute !== "function") throw new TypeError("onRoute must be a function");
  let currentRoute = routeFromHash(windowRef?.location?.hash);
  let started = false;

  const publish = () => onRoute(currentRoute);
  const syncFromLocation = () => {
    currentRoute = routeFromHash(windowRef?.location?.hash);
    publish();
  };

  return Object.freeze({
    get route() { return currentRoute; },
    start() {
      if (started) return currentRoute;
      started = true;
      windowRef?.addEventListener?.("hashchange", syncFromLocation);
      if (!windowRef?.location?.hash && windowRef?.location) {
        windowRef.location.hash = routeToHash(ApplicationRoute.RUNTIME_GATEWAY);
      }
      currentRoute = routeFromHash(windowRef?.location?.hash);
      publish();
      return currentRoute;
    },
    navigate(route) {
      const hash = routeToHash(route);
      currentRoute = route;
      if (windowRef?.location) {
        windowRef.location.hash = hash;
      }
      publish();
      return currentRoute;
    },
    back() {
      if (windowRef?.history?.length > 1 && typeof windowRef.history.back === "function") {
        windowRef.history.back();
        return currentRoute;
      }
      return this.navigate(ApplicationRoute.RUNTIME_GATEWAY);
    },
    dispose() {
      windowRef?.removeEventListener?.("hashchange", syncFromLocation);
      started = false;
    },
  });
}
