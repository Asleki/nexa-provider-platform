/** P006.7.11.9 — Resolve the public HTTPS/localhost API endpoint without database knowledge. */

function normalizeExplicit(value) {
  const text = String(value ?? "").trim();
  if (!text) return "";
  const parsed = new URL(text);
  const local = ["localhost", "127.0.0.1", "::1"].includes(parsed.hostname);
  if (parsed.protocol !== "https:" && !(local && parsed.protocol === "http:")) {
    throw new Error("live API endpoint must use HTTPS outside loopback development");
  }
  return parsed.toString().replace(/\/$/, "");
}

export function resolveLiveApiBaseUrl({ apiBaseUrl = "", windowRef = globalThis.window } = {}) {
  const explicit = normalizeExplicit(apiBaseUrl);
  if (explicit) return explicit;

  const location = windowRef?.location;
  const hostname = String(location?.hostname ?? "").trim();
  const protocol = String(location?.protocol ?? "").trim();
  if (!hostname || !protocol) return "";

  if (["localhost", "127.0.0.1", "::1"].includes(hostname)) {
    if (protocol !== "http:" && protocol !== "https:") return "";
    const host = hostname.includes(":") ? `[${hostname}]` : hostname;
    return `${protocol}//${host}:8000`;
  }

  if (protocol !== "https:") return "";
  return String(location.origin || `${protocol}//${hostname}`).replace(/\/$/, "");
}
