/** P006.UI.10.1.1 — Account creation is enrollment only; authentication remains under Production. */
import { AccountEnrollmentRoute } from "../../app/account/account-enrollment-route.js";

export function accountEnrollmentHomeEntryMarkup() {
  return `
    <section class="account-home-entry" data-account-enrollment-entry aria-labelledby="account-home-entry-title">
      <div>
        <p class="section-kicker">Account</p>
        <h2 id="account-home-entry-title">Create your NexiLabs account</h2>
        <p>Set up a Guest account or begin governed NexaDevs Developer enrollment.</p>
      </div>
      <button class="secondary-button account-home-action" type="button" data-account-route="${AccountEnrollmentRoute.GATEWAY}">Create Account</button>
    </section>`;
}

export function accountEnrollmentGatewayMarkup() {
  return `
    <section class="entry-page account-page" aria-labelledby="account-enrollment-title">
      <p class="eyebrow">NexiLabs Account</p>
      <h1 id="account-enrollment-title">Your NexiLabs Account</h1>
      <p class="summary">Create or verify an account enrollment. Sign in remains under Production access.</p>

      <div class="account-choice-grid">
        <article class="account-choice-card">
          <div>
            <p class="section-kicker">Guest</p>
            <h2>Create Guest account</h2>
            <p>Create a NexiLabs Guest account for future Production client and observational access.</p>
          </div>
          <button class="primary-button" type="button" data-account-route="${AccountEnrollmentRoute.GUEST_CREATE}">Create Guest account</button>
        </article>

        <article class="account-choice-card">
          <div>
            <p class="section-kicker">NexaDevs Developer</p>
            <h2>Governed Developer enrollment</h2>
            <p>Request Developer access or verify an approved Developer Setup issued by NexiLabs.</p>
          </div>
          <div class="account-action-stack">
            <button class="primary-button" type="button" data-account-route="${AccountEnrollmentRoute.DEVELOPER_REQUEST}">Request Developer access</button>
            <button class="secondary-button" type="button" data-account-route="${AccountEnrollmentRoute.DEVELOPER_VERIFY_SETUP}">Verify Developer Setup</button>
          </div>
        </article>
      </div>

      <a class="text-button account-home-link" href="#/runtime">← Return to NexiLabs Home</a>
    </section>`;
}
