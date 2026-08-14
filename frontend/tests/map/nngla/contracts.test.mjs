import test from "node:test";
import assert from "node:assert/strict";
import { assertPublicNnglaFamily, assertPublicNnglaStatus } from "../../../src/map/nngla/contracts.js";

test("P006.7.9 status contract preserves authority and source/canonical/publication count invariants", () => {
  const payload = { authorityId: "authority:nngla", countryId: "country:novegeo", databaseAuthority: "SERVER_SIDE_ONLY", liveDatabaseMigrationStatus: "NOT_EXECUTED", families: [{ family: "ROAD", sourceCount: 900, canonicalCount: 0, publishedCount: 0, mapRenderableCount: 0 }] };
  assert.equal(assertPublicNnglaStatus(payload), payload);
  assert.throws(() => assertPublicNnglaStatus({ ...payload, families: [{ family: "ROAD", sourceCount: 1, canonicalCount: 2, publishedCount: 0, mapRenderableCount: 0 }] }), /Inconsistent/);
  assert.throws(() => assertPublicNnglaStatus({ ...payload, families: [{ family: "ROAD", sourceCount: 2, canonicalCount: 1, publishedCount: 2, mapRenderableCount: 0 }] }), /Inconsistent/);
});

test("P006.7.9 public item contract blocks holder disclosure and fake map readiness", () => {
  assert.throws(() => assertPublicNnglaFamily({ items: [{ publicEligible: true, mapRenderable: true, geometryReference: null }] }), /geometryReference/);
  assert.throws(() => assertPublicNnglaFamily({ items: [{ publicEligible: true, mapRenderable: false, geometryReference: null, holderReference: "citizen:1" }] }), /title-holder/);
});
