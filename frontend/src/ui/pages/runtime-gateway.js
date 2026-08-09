/** P006.UI.2 — NexiLabs runtime gateway landing page. */
import { ApplicationRoute } from "../../app/navigation/application-route.js";
import { SelectedRuntime } from "../../app/navigation/runtime-selection.js";

export function runtimeGatewayMarkup() {
  return `
    <section class="entry-page runtime-gateway" aria-labelledby="runtime-gateway-title">
      <p class="eyebrow">NexiLabs</p>
      <h1 id="runtime-gateway-title">Welcome to NexiLabs</h1>
      <p class="summary">Select a runtime to continue.</p>
      <div class="entry-choice-grid" aria-label="Runtime choices">
        <button class="entry-choice-card" type="button" data-select-runtime="${SelectedRuntime.SIMULATION}" data-route="${ApplicationRoute.SIMULATION_ENTRY}">
          <strong>Simulation</strong>
          <span>Enter the simulated NexiLabs world.</span>
        </button>
        <button class="entry-choice-card" type="button" data-select-runtime="${SelectedRuntime.PRODUCTION}" data-route="${ApplicationRoute.PRODUCTION_ACCESS}">
          <strong>Production</strong>
          <span>Access governed NexiLabs systems and data.</span>
        </button>
      </div>
    </section>`;
}
