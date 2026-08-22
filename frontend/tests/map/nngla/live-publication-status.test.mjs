import test from "node:test";
import assert from "node:assert/strict";
import { mountLiveNnglaPublicationStatus } from "../../../src/map/nngla/live-publication-status.js";

function fakeDocument() {
  const page = { children: [], append(node) { this.children.push(node); } };
  return {
    querySelector(selector) { return selector === ".novegeo-feature-page" ? page : null; },
    createElement() { return { className: "", dataset: {}, innerHTML: "", attributes: {}, setAttribute(k, v) { this.attributes[k] = v; }, remove() { this.removed = true; } }; },
    page,
  };
}

const families = [
  ["PLACE", 700, 700], ["ADMINISTRATIVE_AREA", 192, 192], ["GEOGRAPHIC_FEATURE", 21, 21], ["ROAD", 900, 350], ["ADDRESS", 0, 0], ["PARCEL", 0, 0],
].map(([family, sourceCount, canonicalCount]) => ({ family, sourceCount, canonicalCount, publishedCount: 0, mapRenderableCount: 0 }));

const liveStatus = { authorityId: "authority:nngla", countryId: "country:novegeo", databaseAuthority: "SERVER_SIDE_ONLY", liveDatabaseMigrationStatus: "EXECUTED", readRuntime: "simulation", readModelVersion: 1, families };

test("Bundle 18 live status panel refuses to claim bundled geography when API base is absent", () => {
  const documentRef = fakeDocument();
  const receipt = mountLiveNnglaPublicationStatus({ documentRef, fetchRef: async () => { throw new Error("must not fetch"); } });
  assert.equal(receipt.status, "DEGRADED");
  assert.match(documentRef.page.children[0].innerHTML, /not being promoted as current national authority/i);
});

test("Bundle 18 live status panel displays migrated PostgreSQL canonical truth", async () => {
  const documentRef = fakeDocument();
  const receipt = mountLiveNnglaPublicationStatus({ documentRef, apiBaseUrl: "http://localhost:8000", fetchRef: async () => ({ ok: true, status: 200, async json() { return liveStatus; } }) });
  assert.equal(receipt.status, "LOADING");
  await receipt.ready;
  const panel = documentRef.page.children[0];
  assert.equal(panel.dataset.status, "READY");
  assert.match(panel.innerHTML, /700 canonical \/ 700 source/);
  assert.match(panel.innerHTML, /350 canonical \/ 900 source/);
  assert.match(panel.innerHTML, /EXECUTED/);
});
