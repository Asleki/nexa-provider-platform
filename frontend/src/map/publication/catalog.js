/** P004.M1.5 governed v002 multi-resolution publication catalogue. */
import { validateWorldBoundaryPublication } from "../geography/contracts.js";
import { validatePublicationManifest, MapResolutionClass, DEFAULT_MAP_RESOLUTION } from "./contracts.js";
import { OVERVIEW_WORLD_BOUNDARY_PUBLICATION } from "./v002-overview.js";
import { STANDARD_WORLD_BOUNDARY_PUBLICATION } from "./v002-standard.js";

export const NOVEGEO_V002_PUBLICATION_MANIFEST = Object.freeze({"publicationId":"publication:novegeo:world-boundary:v002","publicationVersion":2,"boundaryId":"boundary:novegeo:sovereign","boundaryVersion":2,"datasetId":"dataset:novegeo:world-boundary","datasetVersion":2,"qualificationId":"qualification:novegeo:world-boundary:v002","qualificationReceiptSha256":"f1795df86bda514e88d714e4d7300c23443b4d55d637b9c7a73b8aacd0b50561","coordinateReference":{"coordinateReferenceId":"crs:novegeo:geographic","version":1,"authorityName":"EPSG","authorityCode":"4326","axisOrder":["longitude","latitude"],"unit":"decimal_degrees"},"runtimeMode":"shared_reference","visibility":"public","lifecycleStatus":"published","defaultResolution":"standard","representations":[{"resolutionClass":"overview","derivativeId":"derivative:novegeo:sovereign:v002:overview:v001","derivativeVersion":1,"vertexCount":197,"polygonCount":6,"offshoreIslandCount":5,"geometrySha256":"1af9ab1688d65929f2470c84d0d159f05ecfd89f64d9b5d46b8545d4dbee1f8c","contentSha256":"062e460c3fef5e45ac3d2b56594a61c2343b480bafd2376a0c009e6dd4da3b31","assetPath":"./public/geography/novegeo/world-boundary/v002/overview.geojson"},{"resolutionClass":"standard","derivativeId":"derivative:novegeo:sovereign:v002:standard:v001","derivativeVersion":1,"vertexCount":493,"polygonCount":6,"offshoreIslandCount":5,"geometrySha256":"50cadc25961324b45b682425625ad0841cce6e008b9c997274c198c2144740b4","contentSha256":"a86d2f9ff56287a7237ee1877ea6dfce2d9ab1a2b22f9874842178a67aa68450","assetPath":"./public/geography/novegeo/world-boundary/v002/standard.geojson"}],"sourceAuthoritativeVertexCount":1048,"activation":{"active":true,"activatedByMilestone":"P004.M1.5","predecessorBoundaryVersion":1},"contentSha256":"da471139ca04d257adf265fa101c709b4ff8db4eb085151a44bf3c1686f21eab"});
validatePublicationManifest(NOVEGEO_V002_PUBLICATION_MANIFEST);

const REPRESENTATIONS = Object.freeze({
  [MapResolutionClass.OVERVIEW]: validateWorldBoundaryPublication(OVERVIEW_WORLD_BOUNDARY_PUBLICATION),
  [MapResolutionClass.STANDARD]: validateWorldBoundaryPublication(STANDARD_WORLD_BOUNDARY_PUBLICATION),
});

export function selectWorldBoundaryPublication(resolution = DEFAULT_MAP_RESOLUTION) {
  if (resolution == null || resolution === "") resolution = DEFAULT_MAP_RESOLUTION;
  if (!Object.prototype.hasOwnProperty.call(REPRESENTATIONS, resolution)) {
    throw new RangeError(`unsupported map resolution: ${resolution}`);
  }
  return REPRESENTATIONS[resolution];
}

export function listWorldBoundaryRepresentations() {
  return NOVEGEO_V002_PUBLICATION_MANIFEST.representations.map((item) => Object.freeze({ ...item }));
}
