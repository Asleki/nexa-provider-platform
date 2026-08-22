import test from "node:test";
import assert from "node:assert/strict";
import { assertLiveNnglaFamily, assertLiveNnglaStatus } from "../../../src/map/nngla/live-contracts.js";

const families = [
  ["PLACE", 700, 700],
  ["ADMINISTRATIVE_AREA", 192, 192],
  ["GEOGRAPHIC_FEATURE", 21, 21],
  ["ROAD", 900, 350],
  ["ADDRESS", 0, 0],
  ["PARCEL", 0, 0],
].map(([family, sourceCount, canonicalCount]) => ({ family, sourceCount, canonicalCount, publishedCount: 0, mapRenderableCount: 0, populationState: canonicalCount ? "CANONICAL_NOT_PUBLISHED" : "EMPTY_DAY_ZERO" }));

function status(overrides = {}) {
  return {
    authorityId: "authority:nngla",
    countryId: "country:novegeo",
    databaseAuthority: "SERVER_SIDE_ONLY",
    liveDatabaseMigrationStatus: "EXECUTED",
    readRuntime: "simulation",
    readModelVersion: 1,
    families,
    ...overrides,
  };
}

test("Bundle 18 live NNGLA status accepts truthful migrated canonical counts", () => {
  const value = assertLiveNnglaStatus(status());
  assert.equal(value.families.find((item) => item.family === "PLACE").canonicalCount, 700);
  assert.equal(value.families.find((item) => item.family === "ROAD").sourceCount, 900);
});

test("Bundle 18 does not let the live contract regress to historical NOT_EXECUTED", () => {
  assert.throws(() => assertLiveNnglaStatus(status({ liveDatabaseMigrationStatus: "NOT_EXECUTED" })), /must be EXECUTED/);
});

test("Bundle 18 public family requires runtime-scoped publication projection items", () => {
  const payload = {
    family: "PLACE", count: 1, sourceCount: 700, canonicalCount: 700, publishedCount: 1, mapRenderableCount: 1,
    readRuntime: "simulation", readModelVersion: 1,
    items: [{ family: "PLACE", subjectId: "place:1", publicEligible: true, mapRenderable: true, geometryReference: "NG-GEO-1", publicationReference: "publication:1", runtimeMode: "simulation" }],
  };
  assert.equal(assertLiveNnglaFamily(payload, "PLACE").count, 1);
  assert.throws(() => assertLiveNnglaFamily({ ...payload, items: [{ ...payload.items[0], runtimeMode: "production" }] }, "PLACE"), /runtime scope mismatch/);
});
