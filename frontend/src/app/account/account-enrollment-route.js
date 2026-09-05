/** P006.UI.10.1.1 — Account-enrollment routes remain separate from runtime/authentication routes. */
export const AccountEnrollmentRoute = Object.freeze({
  GATEWAY: "account-enrollment",
  GUEST_CREATE: "account-guest-create",
  GUEST_VERIFY_EMAIL: "account-guest-verify-email",
  GUEST_COMPLETE: "account-guest-complete",
  DEVELOPER_REQUEST: "account-developer-request",
  DEVELOPER_REQUESTED: "account-developer-requested",
  DEVELOPER_VERIFY_SETUP: "account-developer-verify-setup",
  DEVELOPER_REGISTER: "account-developer-register",
  DEVELOPER_VERIFY_EMAIL: "account-developer-verify-email",
  DEVELOPER_ENIGMA: "account-developer-enigma",
  DEVELOPER_COMPLETE: "account-developer-complete",
});

const ROUTE_HASH = Object.freeze({
  [AccountEnrollmentRoute.GATEWAY]: "#/account",
  [AccountEnrollmentRoute.GUEST_CREATE]: "#/account/guest/create",
  [AccountEnrollmentRoute.GUEST_VERIFY_EMAIL]: "#/account/guest/verify-email",
  [AccountEnrollmentRoute.GUEST_COMPLETE]: "#/account/guest/complete",
  [AccountEnrollmentRoute.DEVELOPER_REQUEST]: "#/account/developer/request",
  [AccountEnrollmentRoute.DEVELOPER_REQUESTED]: "#/account/developer/requested",
  [AccountEnrollmentRoute.DEVELOPER_VERIFY_SETUP]: "#/account/developer/verify-setup",
  [AccountEnrollmentRoute.DEVELOPER_REGISTER]: "#/account/developer/register",
  [AccountEnrollmentRoute.DEVELOPER_VERIFY_EMAIL]: "#/account/developer/verify-email",
  [AccountEnrollmentRoute.DEVELOPER_ENIGMA]: "#/account/developer/enigma",
  [AccountEnrollmentRoute.DEVELOPER_COMPLETE]: "#/account/developer/complete",
});

const HASH_ROUTE = Object.freeze(
  Object.fromEntries(Object.entries(ROUTE_HASH).map(([route, hash]) => [hash, route])),
);

export function isAccountEnrollmentRoute(value) {
  return Object.values(AccountEnrollmentRoute).includes(value);
}

export function accountEnrollmentRouteToHash(route) {
  if (!isAccountEnrollmentRoute(route)) {
    throw new Error(`Unsupported account-enrollment route: ${route}`);
  }
  return ROUTE_HASH[route];
}

export function accountEnrollmentRouteFromHash(hash) {
  return HASH_ROUTE[String(hash || "").trim()] ?? null;
}
