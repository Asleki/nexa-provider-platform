/** P006.UI.9 — Runtime-scoped browser authentication context; sessionStorage stores only the bearer session id. */
const STORAGE_KEY = "nexilabs.auth.session.v1";

function freezeSession(session) {
  if (!session || typeof session !== "object") return null;
  const permissions = Object.freeze([...(session.permissions || [])]);
  return Object.freeze({ ...session, permissions });
}

export function createAuthenticationContext({
  storage = globalThis.sessionStorage,
} = {}) {
  let current = null;
  let pendingSessionId = null;

  if (storage?.getItem) {
    try {
      const stored = JSON.parse(storage.getItem(STORAGE_KEY));
      if (stored && typeof stored.sessionId === "string" && stored.sessionId) {
        pendingSessionId = stored.sessionId;
      }
    } catch {
      storage?.removeItem?.(STORAGE_KEY);
    }
  }

  return Object.freeze({
    get session() { return current; },
    get authenticated() { return Boolean(current?.sessionId); },
    get pendingSessionId() { return pendingSessionId; },
    accept(session) {
      current = freezeSession(session);
      pendingSessionId = current?.sessionId ?? null;
      if (pendingSessionId) storage?.setItem?.(STORAGE_KEY, JSON.stringify({ sessionId: pendingSessionId }));
      return current;
    },
    clear() {
      current = null;
      pendingSessionId = null;
      storage?.removeItem?.(STORAGE_KEY);
    },
  });
}

export { STORAGE_KEY as AUTH_SESSION_STORAGE_KEY };
