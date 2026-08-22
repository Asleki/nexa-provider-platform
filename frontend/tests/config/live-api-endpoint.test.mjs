import test from "node:test";
import assert from "node:assert/strict";
import { resolveLiveApiBaseUrl } from "../../src/config/live-api-endpoint.js";

test("Bundle 18 uses an explicit safe API base when configured", () => {
  assert.equal(resolveLiveApiBaseUrl({ apiBaseUrl: "https://api.example.test/" }), "https://api.example.test");
  assert.equal(resolveLiveApiBaseUrl({ apiBaseUrl: "http://localhost:8000/" }), "http://localhost:8000");
});

test("Bundle 18 derives the conventional local FastAPI port without inventing database access", () => {
  const windowRef = { location: { hostname: "127.0.0.1", protocol: "http:", origin: "http://127.0.0.1:8765" } };
  assert.equal(resolveLiveApiBaseUrl({ windowRef }), "http://127.0.0.1:8000");
});

test("Bundle 18 uses same-origin HTTPS in hosted environments and rejects insecure public endpoints", () => {
  const windowRef = { location: { hostname: "novegeo.nexaecosystem.com", protocol: "https:", origin: "https://novegeo.nexaecosystem.com" } };
  assert.equal(resolveLiveApiBaseUrl({ windowRef }), "https://novegeo.nexaecosystem.com");
  assert.throws(() => resolveLiveApiBaseUrl({ apiBaseUrl: "http://api.example.test" }), /HTTPS outside loopback/);
});
