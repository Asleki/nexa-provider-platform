/** P006.UI.4 — Browser client for the private local development auth authority. */
export class AuthenticationClientError extends Error {
  constructor(message, { status = 0 } = {}) {
    super(message);
    this.name = "AuthenticationClientError";
    this.status = status;
  }
}

export function defaultDevelopmentAuthBase(windowRef = globalThis.window) {
  const hostname = windowRef?.location?.hostname || "127.0.0.1";
  return `http://${hostname}:8766`;
}

export function createDevelopmentAuthClient({
  fetchRef = globalThis.fetch,
  windowRef = globalThis.window,
  baseUrl = defaultDevelopmentAuthBase(windowRef),
} = {}) {
  if (typeof fetchRef !== "function") throw new TypeError("fetchRef must be a function");
  const request = async (path, { method = "GET", body, token } = {}) => {
    const headers = { Accept: "application/json" };
    if (body !== undefined) headers["Content-Type"] = "application/json";
    if (token) headers.Authorization = `Bearer ${token}`;
    let response;
    try {
      response = await fetchRef(`${baseUrl}${path}`, {
        method,
        headers,
        body: body === undefined ? undefined : JSON.stringify(body),
        cache: "no-store",
      });
    } catch (error) {
      throw new AuthenticationClientError("Development authentication authority is unavailable.");
    }
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || payload.ok === false) {
      throw new AuthenticationClientError(payload.error || "Authentication request rejected.", { status: response.status });
    }
    return payload;
  };

  return Object.freeze({
    loginGuest: ({ username, password, runtime }) =>
      request("/auth/guest/login", { method: "POST", body: { username, password, runtime } }),
    startDeveloper: ({ username, password, runtime }) =>
      request("/auth/developer/start", { method: "POST", body: { username, password, runtime } }),
    verifyDeveloper: ({ attemptId, response }) =>
      request("/auth/developer/enigma", { method: "POST", body: { attemptId, response } }),
    session: (token) => request("/auth/session", { token }),
    logout: (token) => request("/auth/logout", { method: "POST", token }),
  });
}
