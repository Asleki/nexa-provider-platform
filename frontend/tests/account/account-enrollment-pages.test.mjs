import test from "node:test";
import assert from "node:assert/strict";
import {
  accountEnrollmentHomeEntryMarkup,
  accountEnrollmentGatewayMarkup,
} from "../../src/ui/pages/account-enrollment-gateway.js";
import {
  guestAccountCreateMarkup,
  guestEmailVerificationMarkup,
  guestAccountCompleteMarkup,
} from "../../src/ui/pages/guest-account-enrollment.js";
import {
  developerAccessRequestMarkup,
  developerRequestReceivedMarkup,
  developerSetupVerificationMarkup,
  developerRegistrationMarkup,
  developerEmailVerificationMarkup,
  developerEnigmaProvisioningMarkup,
  developerAccountCompleteMarkup,
} from "../../src/ui/pages/developer-account-enrollment.js";

function expectFoundationOnly(html) {
  assert.match(html, /Frontend foundation/i);
  assert.doesNotMatch(html, /data-auth-form=/);
}

test("P006.UI.10.1.1 Home adds Create Account as a secondary account entry, not a third runtime card", () => {
  const html = accountEnrollmentHomeEntryMarkup();
  assert.match(html, /Create Account/);
  assert.match(html, /data-account-enrollment-entry/);
  assert.doesNotMatch(html, /entry-choice-card/);
  assert.doesNotMatch(html, /data-select-runtime/);
});

test("P006.UI.10.1.1 account gateway contains enrollment actions only", () => {
  const html = accountEnrollmentGatewayMarkup();
  assert.match(html, /Your NexiLabs Account/);
  assert.match(html, /Create Guest account/);
  assert.match(html, /Request Developer access/);
  assert.match(html, /Verify Developer Setup/);
  assert.doesNotMatch(html, />\s*Sign in\s*</i);
  assert.doesNotMatch(html, /Continue Developer setup/i);
  assert.match(html, /Sign in remains under Production access/i);
});

test("P006.UI.10.1.2 Guest creation reserves identity, email, username and password presentation without authority", () => {
  const html = guestAccountCreateMarkup();
  for (const field of ["firstName", "lastName", "email", "username", "password", "confirmPassword"]) {
    assert.match(html, new RegExp(`name="${field}"`));
  }
  assert.match(html, /data-account-foundation-form="guest-create"/);
  assert.match(html, /Final strength measurement, qualification policy and enforcement belong to the future Production credential authority/i);
  assert.match(html, /data-password-strength-presentation/);
  assert.match(html, /Not evaluated/);
  expectFoundationOnly(html);
});

test("P006.UI.10.1.2 Guest OTP and completion presentations do not claim a working authority", () => {
  const otp = guestEmailVerificationMarkup();
  assert.match(otp, /autocomplete="one-time-code"/);
  assert.match(otp, /No OTP is generated, sent or verified/i);
  assert.match(otp, /Resend code/);
  assert.match(otp, /disabled/);
  expectFoundationOnly(otp);

  const complete = guestAccountCompleteMarkup();
  assert.match(complete, /Return to NexiLabs Home, select Production, then choose Guest to sign in/i);
  assert.match(complete, /does not create a real account/i);
});

test("P006.UI.10.1.3 Developer request collects request identity only", () => {
  const html = developerAccessRequestMarkup();
  assert.match(html, /name="firstName"/);
  assert.match(html, /name="lastName"/);
  assert.match(html, /name="email"/);
  assert.doesNotMatch(html, /name="username"/);
  assert.doesNotMatch(html, /name="password"/);
  assert.doesNotMatch(html, /name="dateOfBirth"/);
  assert.doesNotMatch(html, /name="developerSetupId"/);
  expectFoundationOnly(html);

  const requested = developerRequestReceivedMarkup();
  assert.match(requested, /reserved success presentation/i);
  assert.match(requested, /does not submit a request/i);
});

test("P006.UI.10.1.3 Developer Setup verification remains distinct from credential registration", () => {
  const verify = developerSetupVerificationMarkup();
  assert.match(verify, /Verify Developer Setup/);
  assert.match(verify, /name="developerSetupId"/);
  assert.doesNotMatch(verify, /name="password"/);
  assert.doesNotMatch(verify, /Continue Developer setup/i);
  expectFoundationOnly(verify);

  const register = developerRegistrationMarkup();
  assert.match(register, /name="developerSetupId"[^>]*readonly/);
  assert.match(register, /name="approvedName"[^>]*readonly/);
  assert.match(register, /name="approvedEmail"[^>]*readonly/);
  assert.match(register, /name="username"/);
  assert.match(register, /name="dateOfBirth"/);
  assert.match(register, /name="password"/);
  assert.match(register, /name="confirmPassword"/);
  assert.match(register, /data-password-strength-presentation/);
  assert.match(register, /Not evaluated/);
  expectFoundationOnly(register);
});

test("P006.UI.10.1.3 Developer OTP and Enigma provisioning reserve UI without fabricating secrets", () => {
  const otp = developerEmailVerificationMarkup();
  assert.match(otp, /autocomplete="one-time-code"/);
  assert.match(otp, /No OTP is generated, sent or verified/i);
  expectFoundationOnly(otp);

  const enigma = developerEnigmaProvisioningMarkup();
  assert.match(enigma, /reusable archive password/i);
  assert.match(enigma, /Not yet provisioned/);
  assert.match(enigma, /Copy password/);
  assert.match(enigma, /data-account-copy="enigma-archive-password"[^>]*disabled/);
  assert.match(enigma, /download the protected Enigma credential package/i);
  assert.match(enigma, /No archive password, ZIP\/PDF package or email download link is generated/i);
  assert.doesNotMatch(enigma, /first four|DOB year|date of birth.*archive password/i);
});

test("P006.UI.10.1.3 Developer completion returns authentication to the existing Production path", () => {
  const html = developerAccountCompleteMarkup();
  assert.match(html, /Return to NexiLabs Home, select Production, then choose NexaDevs Developer to sign in/i);
  assert.match(html, /no Developer account is created/i);
});
