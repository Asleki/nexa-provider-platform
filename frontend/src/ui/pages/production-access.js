/** P006.UI.3 — Production access-class choice; authentication is deferred to Bundle 12D. */
import { ApplicationRoute } from "../../app/navigation/application-route.js";

export function productionAccessMarkup() {
  return `
    <section class="entry-page" aria-labelledby="production-access-title">
      <p class="eyebrow">Production</p>
      <h1 id="production-access-title">Choose access</h1>
      <p class="summary">Select the access path that applies to you.</p>
      <div class="entry-choice-grid">
        <button class="entry-choice-card" type="button" data-route="${ApplicationRoute.PRODUCTION_DEVELOPER}">
          <strong>NexaDevs Developer</strong>
          <span>Authorized development and governance access.</span>
        </button>
        <button class="entry-choice-card" type="button" data-route="${ApplicationRoute.PRODUCTION_GUEST}">
          <strong>Guest</strong>
          <span>Client and observational access.</span>
        </button>
      </div>
      <button class="text-button" type="button" data-action="back">← Back</button>
    </section>`;
}
