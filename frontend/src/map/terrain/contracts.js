/** P005.1 governed terrain/elevation browser contracts. */
export const TERRAIN_DATASET_ID = "dataset:novegeo:terrain:elevation";
export const TERRAIN_ID = "terrain:novegeo:surface";
export const ELEVATION_DATUM_ID = "datum:novegeo:elevation:mean-sea-level";
export const TERRAIN_PALETTE = Object.freeze([
  Object.freeze({ max: 350, color: "#655f54" }),
  Object.freeze({ max: 750, color: "#80705b" }),
  Object.freeze({ max: 1200, color: "#9a7f5e" }),
  Object.freeze({ max: 1800, color: "#a77e55" }),
  Object.freeze({ max: 2400, color: "#8f6658" }),
  Object.freeze({ max: Infinity, color: "#d5d0c6" }),
]);
export function validateTerrainPublication(value) {
  if (!value || typeof value !== "object") throw new TypeError("terrain publication must be an object");
  if (value.terrainId !== TERRAIN_ID || value.terrainVersion !== 1) throw new Error("unexpected terrain identity");
  if (value.datasetId !== TERRAIN_DATASET_ID || value.datasetVersion !== 1) throw new Error("unexpected terrain dataset lineage");
  if (value.boundaryId !== "boundary:novegeo:sovereign" || value.boundaryVersion !== 2) throw new Error("terrain must target sovereign boundary v002");
  if (value.coordinateReference?.coordinateReferenceId !== "crs:novegeo:geographic") throw new Error("terrain CRS lineage is invalid");
  if (value.elevationDatum?.elevationDatumId !== ELEVATION_DATUM_ID || value.elevationDatum?.unit !== "metre") throw new Error("terrain elevation datum is invalid");
  if (value.runtimeMode !== "shared_reference") throw new Error("terrain runtime must remain shared_reference");
  if (!Array.isArray(value.samples) || value.samples.length === 0) throw new Error("terrain samples are required");
  return value;
}
export function terrainColorForElevation(metres) {
  if (!Number.isFinite(metres)) throw new TypeError("elevation must be finite");
  return TERRAIN_PALETTE.find((band) => metres <= band.max).color;
}
