/** P003.2/P003.4 — Browser-side service worker registration and recovery boundary. */
export const ServiceWorkerStatus = Object.freeze({
  UNSUPPORTED: "UNSUPPORTED",
  REGISTERING: "REGISTERING",
  REGISTERED: "REGISTERED",
  UPDATE_READY: "UPDATE_READY",
  ACTIVATED: "ACTIVATED",
  FAILED: "FAILED"
});

function renderStatus(documentRef, status) {
  if (!documentRef?.querySelectorAll) return;
  for (const element of documentRef.querySelectorAll("[data-role='pwa-status']")) {
    element.textContent = status.replaceAll("_", " ").toLowerCase();
    element.dataset.pwaStatus = status;
  }
}

export async function registerServiceWorker({
  navigatorRef = globalThis.navigator,
  windowRef = globalThis.window,
  documentRef = globalThis.document,
  scriptUrl = "./sw.js",
  scope = "./"
} = {}) {
  if (!navigatorRef?.serviceWorker?.register) {
    renderStatus(documentRef, ServiceWorkerStatus.UNSUPPORTED);
    return Object.freeze({ supported: false, status: ServiceWorkerStatus.UNSUPPORTED, registration: null });
  }

  renderStatus(documentRef, ServiceWorkerStatus.REGISTERING);
  try {
    const registration = await navigatorRef.serviceWorker.register(scriptUrl, { scope, updateViaCache: "none" });
    let status = registration.waiting ? ServiceWorkerStatus.UPDATE_READY : ServiceWorkerStatus.REGISTERED;
    renderStatus(documentRef, status);

    const announceUpdate = () => {
      status = ServiceWorkerStatus.UPDATE_READY;
      renderStatus(documentRef, status);
      windowRef?.dispatchEvent?.(new CustomEvent("nexilabs:pwa-update-ready"));
    };

    if (registration.waiting) announceUpdate();
    registration.addEventListener?.("updatefound", () => {
      const worker = registration.installing;
      worker?.addEventListener?.("statechange", () => {
        if (worker.state === "installed" && navigatorRef.serviceWorker.controller) announceUpdate();
      });
    });

    navigatorRef.serviceWorker.addEventListener?.("controllerchange", () => {
      status = ServiceWorkerStatus.ACTIVATED;
      renderStatus(documentRef, status);
      windowRef?.dispatchEvent?.(new CustomEvent("nexilabs:pwa-activated"));
    });

    return Object.freeze({
      supported: true,
      get status() { return status; },
      registration,
      activateUpdate() {
        if (!registration.waiting) return false;
        registration.waiting.postMessage({ type: "SKIP_WAITING" });
        return true;
      },
      async checkForUpdate() {
        await registration.update();
        return true;
      }
    });
  } catch (error) {
    renderStatus(documentRef, ServiceWorkerStatus.FAILED);
    return Object.freeze({ supported: true, status: ServiceWorkerStatus.FAILED, registration: null, error });
  }
}
