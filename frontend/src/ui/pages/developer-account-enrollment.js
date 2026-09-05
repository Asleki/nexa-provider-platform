/** P006.UI.10.1.3 — NexaDevs Developer enrollment and Enigma provisioning presentation only. */
import { AccountEnrollmentRoute } from "../../app/account/account-enrollment-route.js";

function foundationNotice(message) {
  return `<div class="account-foundation-note" role="note"><strong>Frontend foundation</strong><p>${message}</p></div>`;
}

export function developerAccessRequestMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="developer-request-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-request-title">Request Developer access</h1>
      <p class="summary">Submit the identity and email NexiLabs will later review before issuing a governed Developer Setup.</p>

      <form class="account-form" data-account-foundation-form="developer-request" data-account-foundation-only="true" novalidate>
        <div class="account-field-grid">
          <label>First name<input name="firstName" autocomplete="given-name" required></label>
          <label>Last name<input name="lastName" autocomplete="family-name" required></label>
        </div>
        <label>Email<input name="email" type="email" autocomplete="email" inputmode="email" required></label>
        <p class="account-authority-message" data-account-authority-message role="status" aria-live="polite"></p>
        <button class="primary-button" type="submit">Submit request</button>
      </form>

      ${foundationNotice("No Developer request is submitted or approved until the later governed account authority exists.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.GATEWAY}">← Account options</button>
    </section>`;
}

export function developerRequestReceivedMarkup() {
  return `
    <section class="entry-page account-page" aria-labelledby="developer-requested-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-requested-title">Developer request received</h1>
      <p class="summary">After future NexiLabs review, an approved Developer Setup will be associated with the submitted email and delivered through the governed enrollment process.</p>
      ${foundationNotice("This is a reserved success presentation; P006.UI.10.1 does not submit a request.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.GATEWAY}">← Account options</button>
    </section>`;
}

export function developerSetupVerificationMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="developer-setup-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-setup-title">Verify Developer Setup</h1>
      <p class="summary">Enter the Developer Setup ID issued after NexiLabs approval.</p>

      <form class="account-form" data-account-foundation-form="developer-setup-verify" data-account-foundation-only="true" novalidate>
        <label>Developer Setup ID<input name="developerSetupId" autocomplete="off" autocapitalize="characters" spellcheck="false" required></label>
        <p class="account-form-help">Future authority will verify approval, expiry, revocation, prior consumption and account association.</p>
        <p class="account-authority-message" data-account-authority-message role="status" aria-live="polite"></p>
        <button class="primary-button" type="submit">Verify Developer Setup</button>
      </form>

      ${foundationNotice("No Setup ID is validated by this frontend-only milestone.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.GATEWAY}">← Account options</button>
    </section>`;
}

export function developerRegistrationMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="developer-register-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-register-title">Create Developer credentials</h1>
      <p class="summary">Approved identity fields become authoritative read-only values after Developer Setup verification.</p>

      <form class="account-form" data-account-foundation-form="developer-register" data-account-foundation-only="true" novalidate>
        <label>Developer Setup ID<input name="developerSetupId" value="" placeholder="Provided after verification" readonly></label>
        <label>Approved name<input name="approvedName" value="" placeholder="Provided after verification" readonly></label>
        <label>Approved email<input name="approvedEmail" type="email" value="" placeholder="Provided after verification" readonly></label>
        <label>Username<input name="username" autocomplete="username" required></label>
        <label>Date of birth<input name="dateOfBirth" type="date" autocomplete="bday" required></label>
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

      ${foundationNotice("No username, DOB or password is stored by P006.UI.10.1. Password policy and persistence belong to the later credential authority.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.DEVELOPER_VERIFY_SETUP}">← Verify Developer Setup</button>
    </section>`;
}

export function developerEmailVerificationMarkup() {
  return `
    <section class="entry-page account-page account-form-page" aria-labelledby="developer-email-verify-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-email-verify-title">Verify approved email</h1>
      <p class="summary">Enter the verification code sent to the approved Developer email.</p>

      <form class="account-form" data-account-foundation-form="developer-email-verify" data-account-foundation-only="true" novalidate>
        <label>Verification code<input name="otp" inputmode="numeric" autocomplete="one-time-code" required></label>
        <p class="account-authority-message" data-account-authority-message role="status" aria-live="polite"></p>
        <div class="account-inline-actions">
          <button class="primary-button" type="submit">Verify email</button>
          <button class="secondary-button" type="button" disabled aria-disabled="true">Resend code</button>
        </div>
      </form>

      ${foundationNotice("No OTP is generated, sent or verified by this milestone.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.DEVELOPER_REGISTER}">← Developer credentials</button>
    </section>`;
}

export function developerEnigmaProvisioningMarkup() {
  return `
    <section class="entry-page account-page account-enigma-provisioning" aria-labelledby="developer-enigma-provision-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-enigma-provision-title">Your NexaDevs Enigma credentials</h1>
      <p class="summary">After future account verification, NexiLabs will provision a protected Enigma credential bundle and a reusable archive password.</p>

      <div class="enigma-provision-card">
        <div>
          <p class="section-kicker">Archive password</p>
          <output class="enigma-archive-password" data-enigma-archive-password aria-live="polite">Not yet provisioned</output>
        </div>
        <button class="secondary-button" type="button" data-account-copy="enigma-archive-password" disabled aria-disabled="true">Copy password</button>
      </div>

      <ol class="account-instructions">
        <li>Copy and securely retain the archive password displayed by NexiLabs.</li>
        <li>Open the verified Developer email account.</li>
        <li>Use the delivered link to download the protected Enigma credential package.</li>
        <li>Use the reusable archive password to extract the downloaded package whenever required.</li>
        <li>Keep the Developer ID, archive password and extracted credential material secured appropriately.</li>
      </ol>

      ${foundationNotice("No archive password, ZIP/PDF package or email download link is generated by P006.UI.10.1.")}
      <button class="text-button" type="button" data-account-route="${AccountEnrollmentRoute.DEVELOPER_VERIFY_EMAIL}">← Email verification</button>
    </section>`;
}

export function developerAccountCompleteMarkup() {
  return `
    <section class="entry-page account-page account-complete-page" aria-labelledby="developer-account-complete-title">
      <p class="eyebrow">NexaDevs Developer</p>
      <h1 id="developer-account-complete-title">Developer account ready</h1>
      <p class="summary">When the future account authority completes enrollment, return to NexiLabs Home, select Production, then choose NexaDevs Developer to sign in.</p>
      ${foundationNotice("This is the completion presentation only; no Developer account is created by P006.UI.10.1.")}
      <a class="primary-button account-link-button" href="#/runtime">Return to NexiLabs Home</a>
    </section>`;
}
