import test from "node:test";
import assert from "node:assert/strict";
import { mountNnglaPublicationStatus } from "../../../src/map/nngla/publication-status.js";

function fakeDocument(apiBaseUrl = "") {
  const page = { children: [], append(node) { this.children.push(node); }, querySelector() { return null; } };
  return {
    documentElement: { dataset: { apiBaseUrl } },
    querySelector(selector) { return selector === ".novegeo-feature-page" ? page : null; },
    createElement() {
      return {
        className: "", dataset: {}, innerHTML: "", attributes: {},
        setAttribute(k, v) { this.attributes[k] = v; },
        remove() { this.removed = true; },
      };
    },
    page,
  };
}

const statusPayload = {
  authorityId: "authority:nngla",
  countryId: "country:novegeo",
  databaseAuthority: "SERVER_SIDE_ONLY",
  liveDatabaseMigrationStatus: "NOT_EXECUTED",
  families: [
    { family: "PLACE", sourceCount: 700, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "KNOWN_NOT_PUBLIC" },
    { family: "ROAD", sourceCount: 900, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "KNOWN_NOT_PUBLIC" },
    { family: "GEOGRAPHIC_FEATURE", sourceCount: 21, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "SOURCE_READY_NOT_MIGRATED" },
    { family: "ADMINISTRATIVE_AREA", sourceCount: 192, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "SOURCE_READY_NOT_MIGRATED" },
    { family: "ADDRESS", sourceCount: 0, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "EMPTY_DAY_ZERO" },
    { family: "PARCEL", sourceCount: 0, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0, populationState: "EMPTY_DAY_ZERO" },
  ],
};

test("P006.7.9 NoveGeo feature degrades safely when no hosted NNGLA API is configured", () => {
  const documentRef = fakeDocument();
  const receipt = mountNnglaPublicationStatus({ documentRef, fetchRef: async () => { throw new Error("must not fetch"); } });
  assert.equal(receipt.status, "DEGRADED");
  assert.equal(documentRef.page.children.length, 1);
  assert.match(documentRef.page.children[0].innerHTML, /offline base map remains available/i);
});

test("P006.7.9 NoveGeo feature renders truthful source/canonical/published/map-ready counts", async () => {
  const documentRef = fakeDocument("https://api.example.test");
  const fetchRef = async () => ({ ok: true, json: async () => statusPayload });
  const receipt = mountNnglaPublicationStatus({ documentRef, fetchRef });
  assert.equal(receipt.status, "LOADING");
  await receipt.ready;
  const panel = documentRef.page.children[0];
  assert.equal(panel.dataset.status, "READY");
  assert.match(panel.innerHTML, /700 places · 900 roads/);
  assert.match(panel.innerHTML, /21 features · 192 admin/);
  assert.match(panel.innerHTML, /PostgreSQL canonical/);
  assert.match(panel.innerHTML, /NOT_EXECUTED/);
  assert.doesNotMatch(panel.innerHTML, /holder|title/i);
});
