import test from "node:test";
import assert from "node:assert/strict";
import { createLiveWorldBoundaryClient } from "../../../src/map/geography/live-boundary-client.js";
import { createNationalMapClient } from "../../../src/map/nngla/national-map-client.js";

const boundary = {
  boundaryId: "boundary:novegeo:sovereign",
  boundaryVersion: 2,
  datasetId: "dataset:novegeo:world-boundary",
  datasetVersion: 2,
  runtimeMode: "shared_reference",
  publicationId: "publication:novegeo:world-boundary:test",
  sourceSha256: "a".repeat(64),
  contentSha256: "b".repeat(64),
  coordinateReference: { coordinateReferenceId: "crs:novegeo:geographic", version: 1, axisOrder: ["longitude", "latitude"] },
  extent: { minLongitude: 29, minLatitude: -8, maxLongitude: 45, maxLatitude: 8 },
  geometry: { type: "MultiPolygon", coordinates: [[[[29,-8],[45,-8],[45,8],[29,8],[29,-8]]]] },
};

function feature(subjectId, family, classificationCode) {
  return {
    subjectId,
    family,
    displayName: subjectId,
    publicationReference: `publication:${subjectId}`,
    publicEligible: true,
    mapRenderable: true,
    geometryId: `geometry:${subjectId}`,
    geometryVersion: 1,
    geometryRole: "BOUNDARY",
    geometryType: "POLYGON",
    crsCode: "NG-CRS-EPSG4326",
    geometry: { type: "Polygon", coordinates: [[[30,0],[31,0],[31,1],[30,0]]] },
    runtimeEffectScope: "SHARED_REFERENCE",
    classificationScheme: "TEST",
    classificationCode,
    readModelVersion: 1,
  };
}

const payload = {
  authorityId: "authority:nngla",
  countryId: "country:novegeo",
  readRuntime: "simulation",
  mapReadModelVersion: 1,
  families: ["PLACE", "ADMINISTRATIVE_AREA", "ROAD", "GEOGRAPHIC_FEATURE"],
  items: [
    feature("NG-ADM-000001", "ADMINISTRATIVE_AREA", "REGION"),
    feature("NG-PLC-000001", "PLACE", "TOWN"),
  ],
  count: 2,
  nextCursor: null,
  semanticChecksum: "c".repeat(64),
};

test("shared loader coalesces one boundary read and one unfiltered 2000-feature read", async () => {
  const seen = [];
  const fetchRef = async (url) => {
    seen.push(String(url));
    if (String(url).includes("world-boundary")) {
      await new Promise((resolve) => setTimeout(resolve, 5));
      return { ok: true, status: 200, json: async () => boundary };
    }
    await new Promise((resolve) => setTimeout(resolve, 5));
    return { ok: true, status: 200, json: async () => payload, headers: { get: () => null } };
  };
  const base = "http://127.0.0.1:8000";
  const boundaryA = createLiveWorldBoundaryClient({ apiBaseUrl: base, fetchRef });
  const boundaryB = createLiveWorldBoundaryClient({ apiBaseUrl: base, fetchRef });
  const mapA = createNationalMapClient({ apiBaseUrl: base, fetchRef });
  const mapB = createNationalMapClient({ apiBaseUrl: base, fetchRef });
  const bounds = boundary.extent;

  const [b1, b2, admin, towns] = await Promise.all([
    boundaryA.getActive(),
    boundaryB.getActive(),
    mapA.readViewport(bounds, { families: ["ADMINISTRATIVE_AREA"], limit: 2000 }),
    mapB.readViewport(bounds, { families: ["PLACE"], limit: 2000 }),
  ]);

  assert.equal(b1.boundaryId, boundary.boundaryId);
  assert.equal(b2.boundaryId, boundary.boundaryId);
  assert.equal(admin.items.length, 1);
  assert.equal(admin.items[0].family, "ADMINISTRATIVE_AREA");
  assert.equal(towns.items.length, 1);
  assert.equal(towns.items[0].family, "PLACE");
  assert.equal(seen.filter((url) => url.includes("world-boundary")).length, 1);
  const mapUrls = seen.filter((url) => url.includes("nngla-map/features"));
  assert.equal(mapUrls.length, 1);
  assert.match(mapUrls[0], /limit=2000/);
  assert.doesNotMatch(mapUrls[0], /family=/);
});

test("shared loader clears failed in-flight reads so later authority recovery can retry", async () => {
  let attempts = 0;
  const fetchRef = async (url) => {
    if (!String(url).includes("world-boundary")) throw new Error("unexpected map request");
    attempts += 1;
    if (attempts === 1) return { ok: false, status: 503, json: async () => ({}) };
    return { ok: true, status: 200, json: async () => boundary };
  };
  const client = createLiveWorldBoundaryClient({ apiBaseUrl: "http://recovery.test", fetchRef });
  await assert.rejects(() => client.getActive(), /503/);
  const recovered = await client.getActive();
  assert.equal(recovered.boundaryVersion, 2);
  assert.equal(attempts, 2);
});
