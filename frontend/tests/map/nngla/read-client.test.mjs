import test from "node:test";
import assert from "node:assert/strict";
import { createNnglaReadClient } from "../../../src/map/nngla/read-client.js";

const statusPayload = Object.freeze({
  authorityId: "authority:nngla",
  countryId: "country:novegeo",
  databaseAuthority: "SERVER_SIDE_ONLY",
  liveDatabaseMigrationStatus: "NOT_EXECUTED",
  families: [{ family: "PLACE", sourceCount: 700, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "SOURCE_READY_NOT_MIGRATED" }],
});

test("P006.7.9 NNGLA client performs read-only status requests through the governed API", async () => {
  const calls = [];
  const fetchRef = async (url, options) => {
    calls.push({ url, options });
    return { ok: true, json: async () => statusPayload };
  };
  const client = createNnglaReadClient({ apiBaseUrl: "https://api.example.test/", fetchRef });
  const body = await client.status();
  assert.equal(body.authorityId, "authority:nngla");
  assert.equal(calls[0].url, "https://api.example.test/api/v1/nngla/status");
  assert.equal(calls[0].options.method, "GET");
});

test("P006.7.9 client rejects browser payloads that imply database authority", async () => {
  const fetchRef = async () => ({ ok: true, json: async () => ({ ...statusPayload, databaseAuthority: "DIRECT_POSTGRESQL" }) });
  await assert.rejects(() => createNnglaReadClient({ fetchRef }).status(), /browser\/database authority boundary/);
});

test("P006.7.9 public family client refuses restricted title family", async () => {
  const client = createNnglaReadClient({ fetchRef: async () => ({ ok: true, json: async () => ({}) }) });
  await assert.rejects(() => client.list("titles"), /Unsupported NNGLA family path/);
});
