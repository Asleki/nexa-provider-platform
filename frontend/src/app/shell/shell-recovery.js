/** Bundle 12.0C — Foreground recovery for incomplete NexiLabs shared shell chrome. */
import { loadShellPartials, shellPartialsReady } from "./partial-loader.js";

export function installShellPartialRecovery({
  documentRef = globalThis.document,
  windowRef = globalThis.window,
  fetchRef = globalThis.fetch,
  onRecovered = () => {},
  timeoutMs,
} = {}) {
  if (!documentRef?.addEventListener) throw new TypeError("documentRef must provide addEventListener");
  if (typeof onRecovered !== "function") throw new TypeError("onRecovered must be a function");

  let disposed = false;
  let inFlight = null;

  const recover = async () => {
    if (disposed || shellPartialsReady(documentRef)) return false;
    if (inFlight) return inFlight;

    inFlight = loadShellPartials({ documentRef, fetchRef, ...(timeoutMs ? { timeoutMs } : {}) })
      .then(() => {
        onRecovered();
        return true;
      })
      .catch(() => false)
      .finally(() => {
        inFlight = null;
      });
    return inFlight;
  };

  const onPageShow = () => { void recover(); };
  const onOnline = () => { void recover(); };
  const onVisibility = () => {
    if (documentRef.visibilityState === "visible") void recover();
  };

  windowRef?.addEventListener?.("pageshow", onPageShow);
  windowRef?.addEventListener?.("online", onOnline);
  documentRef.addEventListener("visibilitychange", onVisibility);

  return Object.freeze({
    recover,
    get ready() { return shellPartialsReady(documentRef); },
    dispose() {
      disposed = true;
      windowRef?.removeEventListener?.("pageshow", onPageShow);
      windowRef?.removeEventListener?.("online", onOnline);
      documentRef.removeEventListener?.("visibilitychange", onVisibility);
    },
  });
}
