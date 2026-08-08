/** P005.5 browser contracts for governed vegetation and arid-zone baseline. */
export const VEGETATION_DATASET_ID="dataset:novegeo:vegetation:baseline";
export const VEGETATION_PALETTE=Object.freeze({
 dense_vegetation:"rgba(35,107,62,0.24)",woodland:"rgba(72,124,67,0.20)",grassland:"rgba(119,139,74,0.17)",sparse_vegetation:"rgba(156,137,76,0.14)",arid_surface:"rgba(178,119,68,0.20)"
});
export function validateVegetationPublication(value){
 if(!value||typeof value!=="object")throw new TypeError("vegetation publication must be an object");
 if(value.biosphereId!=="biosphere:novegeo:vegetation-baseline"||value.biosphereVersion!==1)throw new Error("unexpected vegetation identity");
 if(value.datasetId!==VEGETATION_DATASET_ID||value.datasetVersion!==1)throw new Error("unexpected vegetation dataset lineage");
 if(value.boundaryId!=="boundary:novegeo:sovereign"||value.boundaryVersion!==2)throw new Error("vegetation boundary lineage is invalid");
 if(value.terrainDatasetId!=="dataset:novegeo:terrain:elevation"||value.hydrologyDatasetId!=="dataset:novegeo:hydrology:surface-water"||value.climateDatasetId!=="dataset:novegeo:climate:baseline")throw new Error("vegetation environmental lineage is invalid");
 if(value.runtimeMode!=="shared_reference")throw new Error("vegetation runtime must remain shared_reference");
 if(value.classification?.namingAuthority!=="deferred")throw new Error("vegetation naming authority must remain deferred");
 if(!Array.isArray(value.samples)||value.samples.length<200)throw new Error("vegetation samples are required");
 for(const s of value.samples){if(!/^vegetation:novegeo:cell:\d{6}$/.test(s.vegetationCellId)||"name" in s)throw new Error("vegetation cell identity must be anonymous and stable");if(!(s.vegetationClass in VEGETATION_PALETTE)||!Number.isFinite(s.longitude)||!Number.isFinite(s.latitude))throw new Error("vegetation sample is invalid");}
 return value;
}
export function vegetationColorForClass(value){const color=VEGETATION_PALETTE[value];if(!color)throw new Error("unknown vegetation class");return color;}
