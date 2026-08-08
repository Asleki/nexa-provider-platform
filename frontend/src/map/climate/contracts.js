/** P005.4 browser contracts for governed baseline climate. */
export const CLIMATE_DATASET_ID="dataset:novegeo:climate:baseline";
export function validateClimatePublication(value){
 if(!value||typeof value!=="object") throw new TypeError("climate publication must be an object");
 if(value.climateId!=="climate:novegeo:baseline"||value.climateVersion!==1) throw new Error("unexpected climate identity");
 if(value.datasetId!==CLIMATE_DATASET_ID||value.datasetVersion!==1) throw new Error("unexpected climate dataset lineage");
 if(value.hydrologyDatasetId!=="dataset:novegeo:hydrology:surface-water"||value.hydrologyDatasetVersion!==1) throw new Error("climate hydrology lineage is invalid");
 if(value.runtimeMode!=="shared_reference") throw new Error("climate runtime must remain shared_reference");
 if(value.cartographicModel?.featureNamingAuthority!=="deferred") throw new Error("atmospheric naming authority must remain deferred");
 if(!Array.isArray(value.rainfallSystems)||value.rainfallSystems.length!==2) throw new Error("two governed rainfall systems are required");
 for(const system of value.rainfallSystems){
  if(!/^rainfall:novegeo:rs\d{6}$/.test(system.rainfallSystemId)||"name" in system) throw new Error("rainfall system identity must be anonymous and stable");
  if(system.fieldModel?.type!=="irregular_radial_intensity"||system.fieldModel?.visibleBoundary!==false) throw new Error("rainfall system must use invisible irregular intensity field");
  if(!Number.isFinite(system.referencePoint?.longitude)||!Number.isFinite(system.referencePoint?.latitude)) throw new Error("rainfall reference point is invalid");
 }
 const systems=[...value.rainfallSystems].sort((a,b)=>a.relativePower-b.relativePower);
 if(systems[0].intensityClass!=="strong"||systems[1].intensityClass!=="powerful") throw new Error("rainfall intensity classes are invalid");
 if(!(systems[1].peakAnnualRainfallMm>systems[0].peakAnnualRainfallMm)) throw new Error("powerful rainfall must exceed strong rainfall");
 if(!Array.isArray(value.samples)||value.samples.length<200) throw new Error("climate samples are required");
 return value;
}
export const CLIMATE_PALETTE=Object.freeze([
 Object.freeze({max:850,color:"rgba(196,157,74,0.10)"}),
 Object.freeze({max:1200,color:"rgba(112,171,158,0.12)"}),
 Object.freeze({max:1700,color:"rgba(65,156,190,0.14)"}),
 Object.freeze({max:Infinity,color:"rgba(38,126,194,0.17)"}),
]);
export function climateColorForRainfall(mm){ if(!Number.isFinite(mm)) throw new TypeError("rainfall must be finite"); return CLIMATE_PALETTE.find(b=>mm<=b.max).color; }
