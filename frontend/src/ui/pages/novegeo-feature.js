/** P006.UI.13 — Runtime-aware NoveGeo feature-page shell around the locked map engine. */

export function noveGeoFeatureMarkup({ runtime = "simulation", backRoute = "simulation-entry" } = {}) {
  const production = runtime === "production";
  return `
    <section class="novegeo-feature-page" data-runtime="${runtime}" aria-labelledby="novegeo-feature-title">
      <header class="novegeo-feature-heading">
        <div>
          <p class="eyebrow">${production ? "Production" : "Simulation"} · NoveGeo</p>
          <h1 id="novegeo-feature-title">NoveGeo</h1>
        </div>
        <button class="text-button compact-back" type="button" data-route="${backRoute}">← Workspace</button>
      </header>

      <div class="novegeo-map-stage" data-role="novegeo-map-stage">
        <div class="novegeo-map-viewport" data-role="future-map-viewport" aria-label="Interactive NoveGeo map">
          <span class="sr-only" data-role="map-render-status" aria-live="polite">Preparing map</span>
        </div>
        <div class="novegeo-tool-rail" data-role="novegeo-tool-rail" aria-label="Map tools"></div>
      </div>
      <p class="privacy-note" data-role="novegeo-authority-state" role="status" aria-live="polite">Connecting to the authoritative NoveGeo read API…</p>
      <p class="novegeo-feature-note">Governed geography only. No citizen, business, institution or population overlays are introduced by Bundle 12E.</p>
    </section>`;
}
