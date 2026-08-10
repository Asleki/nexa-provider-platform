/** P006.UI.11 — Production Guest Workspace with future citizen/business relationships reserved. */
import { ApplicationRoute } from "../../app/navigation/application-route.js";
import { GUEST_CAPABILITIES, CapabilityAvailability } from "../../app/workspaces/workspace-capabilities.js";

function esc(value) {
  return String(value ?? "").replace(/[&<>\"]/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[ch]));
}

function capabilityCard(item) {
  const available = item.availability === CapabilityAvailability.AVAILABLE;
  const action = available && item.route === "production-novegeo"
    ? `<button class="workspace-action" type="button" data-route="${ApplicationRoute.PRODUCTION_NOVEGEO}">Open NoveGeo</button>`
    : `<span class="workspace-status" data-availability="${item.availability}">${item.availability}</span>`;
  return `<article class="workspace-capability-card" data-capability="${item.id}">
    <div><h2>${esc(item.title)}</h2><p>${esc(item.description)}</p></div>${action}
  </article>`;
}

export function productionGuestWorkspaceMarkup(session) {
  return `
    <section class="workspace-page" aria-labelledby="guest-workspace-title">
      <header class="workspace-heading">
        <p class="eyebrow">Production · Guest</p>
        <h1 id="guest-workspace-title">Production Guest Workspace</h1>
        <p class="summary">Your governed NexiLabs client context. Citizen and Business identities remain future relationships, not alternate Guest login types.</p>
      </header>

      <section class="workspace-section" aria-labelledby="guest-systems-title">
        <div class="workspace-section-heading"><p class="section-kicker">Available systems</p><h2 id="guest-systems-title">Production access</h2></div>
        <div class="workspace-capability-grid">${GUEST_CAPABILITIES.map(capabilityCard).join("")}</div>
      </section>

      <section class="workspace-section workspace-identity" aria-labelledby="guest-account-title">
        <div class="workspace-section-heading"><p class="section-kicker">Account</p><h2 id="guest-account-title">Guest context</h2></div>
        <dl class="workspace-facts">
          <div><dt>Principal</dt><dd>${esc(session?.principalId)}</dd></div>
          <div><dt>Runtime</dt><dd>${esc(session?.runtime || "production")}</dd></div>
          <div><dt>Session</dt><dd>Active</dd></div>
        </dl>
      </section>

      <button class="primary-button" type="button" data-auth-action="logout">Sign out</button>
    </section>`;
}
