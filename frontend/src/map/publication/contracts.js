/** P004.M1.5 multi-resolution publication contracts. */

export const MapResolutionClass = Object.freeze({ OVERVIEW: "overview", STANDARD: "standard" });
export const DEFAULT_MAP_RESOLUTION = MapResolutionClass.STANDARD;

export function validatePublicationManifest(value) {
  if (!value || typeof value !== "object") throw new TypeError("publication manifest must be an object");
  if (value.publicationId !== "publication:novegeo:world-boundary:v002") throw new Error("unexpected publication identity");
  if (value.boundaryId !== "boundary:novegeo:sovereign" || value.boundaryVersion !== 2) throw new Error("publication must activate sovereign boundary v002");
  if (value.datasetId !== "dataset:novegeo:world-boundary" || value.datasetVersion !== 2) throw new Error("publication dataset lineage is invalid");
  if (value.qualificationId !== "qualification:novegeo:world-boundary:v002") throw new Error("publication qualification lineage is invalid");
  if (value.runtimeMode !== "shared_reference" || value.visibility !== "public") throw new Error("publication runtime/visibility is invalid");
  if (!Array.isArray(value.representations) || value.representations.length < 2) throw new Error("multi-resolution representations are required");
  return value;
}
