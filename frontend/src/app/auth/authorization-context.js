/** P006.UI.9 — Authorization remains separate from authentication. */
export function createAuthorizationContext(authenticationContext) {
  if (!authenticationContext) throw new TypeError("authenticationContext is required");
  return Object.freeze({
    permissions() {
      return Object.freeze([...(authenticationContext.session?.permissions || [])]);
    },
    can(permission) {
      return (authenticationContext.session?.permissions || []).includes(permission);
    },
    identityType() {
      return authenticationContext.session?.identityType ?? null;
    },
    runtime() {
      return authenticationContext.session?.runtime ?? null;
    },
  });
}
