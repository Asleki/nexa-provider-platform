/** P006.UI.12 — Public-facing Simulation Workspace; read-heavy and privacy-safe by default. */
import { ApplicationRoute } from "../../app/navigation/application-route.js";
import { SIMULATION_CAPABILITIES, CapabilityAvailability } from "../../app/workspaces/workspace-capabilities.js";

function capabilityCard(item) {
  const available = item.availability === CapabilityAvailability.AVAILABLE;
  const action = available && item.route === "simulation-novegeo"
    ? `<button class="workspace-action" type="button" data-route="${ApplicationRoute.SIMULATION_NOVEGEO}">Explore map</button>`
    : `<span class="workspace-status" data-availability="${item.availability}">${item.availability}</span>`;
  return `<article class="workspace-capability-card" data-capability="${item.id}">
    <div><h2>${item.title}</h2><p>${item.description}</p></div>${action}
  </article>`;
}

export function simulationWorkspaceMarkup() {
  return `
    <section class="workspace-page simulation-workspace" aria-labelledby="simulation-workspace-title">
      <header class="workspace-heading">
        <p class="eyebrow">Simulation · Public world</p>
        <h1 id="simulation-workspace-title">Explore NexiLabs</h1>
        <p class="summary">Simulation is the public-facing NexiLabs experience. It is predominantly observational today, with future governed interactions added without crossing into Production authority.</p>
      </header>

      <section class="workspace-section" aria-labelledby="simulation-now-title">
        <div class="workspace-section-heading"><p class="section-kicker">Available now</p><h2 id="simulation-now-title">Public simulation surface</h2></div>
        <div class="workspace-capability-grid">${SIMULATION_CAPABILITIES.map(capabilityCard).join("")}</div>
      </section>

      <aside class="privacy-note" role="note">
        <strong>Public visibility boundary</strong>
        <p>Future public map views may show places, structures and public addresses, but they must not automatically combine a house, an address and a private citizen identity. Unrestricted citizen-name search is outside this public workspace.</p>
      </aside>

      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
