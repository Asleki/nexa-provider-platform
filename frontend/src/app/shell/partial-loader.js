/** P006.UI.1 — Shared HTML partial loader for NexiLabs chrome. */
export const ShellPartial = Object.freeze({
  HEADER: Object.freeze({ slot: "[data-shell-slot='header']", url: "./src/ui/partials/header.html" }),
  FOOTER: Object.freeze({ slot: "[data-shell-slot='footer']", url: "./src/ui/partials/footer.html" }),
});

export async function loadPartial({ documentRef, fetchRef = globalThis.fetch, descriptor }) {
  if (!documentRef?.querySelector) throw new TypeError("documentRef must provide querySelector");
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const slot = documentRef.querySelector(descriptor.slot);
  if (!slot) throw new Error(`Shell partial slot not found: ${descriptor.slot}`);
  const response = await fetchRef(descriptor.url, { cache: "no-cache" });
  if (!response?.ok) throw new Error(`Failed to load shell partial: ${descriptor.url}`);
  slot.innerHTML = await response.text();
  slot.dataset.partialReady = "true";
  return Object.freeze({ slot: descriptor.slot, url: descriptor.url, ready: true });
}

export async function loadShellPartials(options = {}) {
  return Promise.all([
    loadPartial({ ...options, descriptor: ShellPartial.HEADER }),
    loadPartial({ ...options, descriptor: ShellPartial.FOOTER }),
  ]);
}
