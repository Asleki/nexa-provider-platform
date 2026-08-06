/** Bundled public-safe P004.1 authority fixture used until the P008 API client exists. */
import { COORDINATE_REFERENCE, validateWorldBoundaryPublication } from "../geography/contracts.js";

export const BUNDLED_WORLD_BOUNDARY_PUBLICATION = validateWorldBoundaryPublication({
  publicationId: "publication:novegeo:world-boundary:v001",
  boundaryId: "boundary:novegeo:sovereign",
  boundaryVersion: 1,
  datasetId: "dataset:novegeo:world-boundary",
  datasetVersion: 1,
  coordinateReference: COORDINATE_REFERENCE,
  geometry: {
    type: "MultiPolygon",
    coordinates: [[[[30, -6], [36, -8], [42, -4], [45, 2], [41, 7], [34, 8], [29, 3], [30, -6]]]],
  },
  extent: Object.freeze({
    minLongitude: 29,
    minLatitude: -8,
    maxLongitude: 45,
    maxLatitude: 8,
  }),
  runtimeMode: "shared_reference",
  sourceSha256: "d6b9764dd7be827d714dfc7cd0e8a2ad986907ab08b094fc3257408ae9bde582",
  contentSha256: "c579d0566d8fc55311901c7febad2ed97b5f9f84224d6db89483b2512bb296c6",
});
