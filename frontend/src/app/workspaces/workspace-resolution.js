/** P006.UI.10-P006.UI.12 — Resolve runtime + authenticated identity into one workspace kind. */

export const WorkspaceKind = Object.freeze({
  PRODUCTION_DEVELOPER: "production-developer",
  PRODUCTION_GUEST: "production-guest",
  SIMULATION_PUBLIC: "simulation-public",
});

export function resolveProductionWorkspace(session) {
  if (!session?.sessionId) return null;
  if (session.runtime !== "production") return null;
  if (session.identityType === "nexadevs_developer") return WorkspaceKind.PRODUCTION_DEVELOPER;
  if (session.identityType === "guest") return WorkspaceKind.PRODUCTION_GUEST;
  return null;
}
