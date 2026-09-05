/** P006.UI.10.1.2 — Guest enrollment presentation; no account authority is implemented here. */
import { AccountEnrollmentRoute } from "../../app/account/account-enrollment-route.js";

function foundationNotice(nextStep) {
  return `<div class="account-foundation-note" role="note">
    <strong>Frontend foundation</strong>
    <p>This step does not yet submit or retain account data. ${nextStep}</p>
  </div>`;
}

export function guestAccountCreateMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="guest-account-create-title">
      <p class="eyebrow">NexiLabs Account · Guest</p>
      <h1 id="guest-account-create-title">Create Guest account</h1>
      <p class="summary">Prepare the identity and sign-in details for a future NexiLabs Guest account.</p>

      <form class="account-form" data-account-foundation-form="guest-create" data-account-foundation-only="true" novalidate>
        <div class="account-field-grid">
          <label>First name<input name="firstName" autocomplete="given-name" required></label>
          <label>Last name<input name="lastName" autocomplete="family-name" required></label>
        </div>
        <label>Email<input name="email" type="email" autocomplete="email" inputmode="email" required></label>
        <label>Username<input name="username" autocomplete="username" required></label>
        <label>Password<input name="password" type="password" autocomplete="new-password" required></label>
        <label>Confirm password<input name="confirmPassword" type="password" autocomplete="new-password" required></label>

        <div class="password-requirements" data-password-strength-presentation aria-label="Future password strength presentation">
          <strong>Password strength</strong>
          <output data-password-strength>Not evaluated</output>
          <p>Final strength measurement, qualification policy and enforcement belong to the future Production credential authority.</p>
        </div>

        <p class="account-authority-message" data-account-authority-message role="status" aria-live="polite"></p>
        <button class="primary-button" type="submit">Continue</button>
      </form>

      ${foundationNotice("Email verification will become reachable only after the account authority accepts this form.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.GATEWAY}">← Account options</button>
    </section>`;
}

export function guestEmailVerificationMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="guest-email-verify-title">
      <p class="eyebrow">NexiLabs Account · Guest</p>
      <h1 id="guest-email-verify-title">Verify your email</h1>
      <p class="summary">Enter the verification code sent to the email associated with your Guest enrollment.</p>

      <form class="account-form" data-account-foundation-form="guest-email-verify" data-account-foundation-only="true" novalidate>
        <label>Verification code<input name="otp" inputmode="numeric" autocomplete="one-time-code" required></label>
        <p class="account-form-help">Code expiry, retry limits and resend authority are reserved for the later OTP service.</p>
        <p class="account-authority-message" data-account-authority-message role="status" aria-live="polite"></p>
        <div class="account-inline-actions">
          <button class="primary-button" type="submit">Verify email</button>
          <button class="secondary-button" type="button" disabled aria-disabled="true">Resend code</button>
        </div>
      </form>

      ${foundationNotice("No OTP is generated, sent or verified by P006.UI.10.1.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.GUEST_CREATE}">← Guest account details</button>
    </section>`;
}

export function guestAccountCompleteMarkup() {
  return `
    <section class="entry-page account-page account-complete-page" aria-labelledby="guest-account-complete-title">
      <p class="eyebrow">NexiLabs Account · Guest</p>
      <h1 id="guest-account-complete-title">Guest account created</h1>
      <p class="summary">When the future account authority completes enrollment, return to NexiLabs Home, select Production, then choose Guest to sign in.</p>
      ${foundationNotice("This is the completion presentation only; P006.UI.10.1 does not create a real account.")}
      <a class="primary-button account-link-button" href="#/runtime">Return to NexiLabs Home</a>
    </section>`;
}
