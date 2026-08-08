/** P005.3 browser contracts for governed surface hydrology. */
export const HYDROLOGY_DATASET_ID="dataset:novegeo:hydrology:surface-water";
const pair=p=>[Number(p?.longitude),Number(p?.latitude)];
const same=(a,b)=>a[0]===b[0]&&a[1]===b[1];
export function validateHydrologyPublication(value){
 if(!value||typeof value!=="object") throw new TypeError("hydrology publication must be an object");
 if(value.hydrologyId!=="hydrology:novegeo:surface-water"||value.hydrologyVersion!==1) throw new Error("unexpected hydrology identity");
 if(value.datasetId!==HYDROLOGY_DATASET_ID||value.datasetVersion!==1) throw new Error("unexpected hydrology dataset lineage");
 if(value.boundaryId!=="boundary:novegeo:sovereign"||value.boundaryVersion!==2) throw new Error("hydrology must target sovereign boundary v002");
 if(value.terrainDatasetId!=="dataset:novegeo:terrain:elevation"||value.terrainDatasetVersion!==1) throw new Error("hydrology terrain lineage is invalid");
 if(value.runtimeMode!=="shared_reference") throw new Error("hydrology runtime must remain shared_reference");
 if(value.cartographicModel?.anonymousFeatureIdentity!==true||value.cartographicModel?.featureNamingAuthority!=="deferred") throw new Error("hydrology naming authority must remain deferred");
 if(value.cartographicModel?.riverTopology!=="exact_shared_coordinate_confluences") throw new Error("hydrology confluences must use exact shared coordinates");
 if(value.cartographicModel?.lakeConnectivity!=="closed_basins_without_distributaries") throw new Error("v001 lakes must remain without distributaries");
 if(!Array.isArray(value.rivers)||value.rivers.length<4||!Array.isArray(value.lakes)||value.lakes.length<2||!Array.isArray(value.junctions)||value.junctions.length<1) throw new Error("hydrology publication is incomplete");
 const rivers=new Map(value.rivers.map(r=>[r.riverId,r]));
 const junctions=new Map(value.junctions.map(j=>[j.junctionId,j]));
 for(const river of value.rivers){
  if(!/^river:novegeo:r\d{6}$/.test(river.riverId)||"name" in river) throw new Error("river identity must be anonymous and stable");
  if(!["tributary","secondary","principal"].includes(river.riverClass)||![1,2,3].includes(river.streamOrder)) throw new Error("river hierarchy is invalid");
  if(!Array.isArray(river.geometry?.coordinates)||river.geometry.coordinates.length<20) throw new Error("river geometry must be densified");
  if(!Number.isFinite(river.referencePoint?.longitude)||!Number.isFinite(river.referencePoint?.latitude)) throw new Error("river reference point is invalid");
  if(river.downstreamJunctionId){
   const j=junctions.get(river.downstreamJunctionId),receiver=rivers.get(river.downstreamRiverId);if(!j||!receiver) throw new Error("river downstream topology reference is unknown");
   const jc=pair(j.coordinate),end=river.geometry.coordinates.at(-1);if(!same(end,jc)||!receiver.geometry.coordinates.some(c=>same(c,jc))) throw new Error("confluence must use an exact shared coordinate");
  }
 }
 for(const lake of value.lakes){
  if(!/^lake:novegeo:l\d{6}$/.test(lake.lakeId)||"name" in lake) throw new Error("lake identity must be anonymous and stable");
  if(!Number.isFinite(lake.referencePoint?.longitude)||!Number.isFinite(lake.referencePoint?.latitude)) throw new Error("lake reference point is invalid");
  if(lake.hydrologicRole!=="closed_basin_lake"||lake.surfaceOutlet!=="none_declared") throw new Error("v001 lakes must remain without distributaries");
 }
 for(const j of value.junctions){if(!/^junction:novegeo:j\d{6}$/.test(j.junctionId)||j.junctionType!=="confluence"||!Number.isFinite(j.coordinate?.longitude)||!Number.isFinite(j.coordinate?.latitude)) throw new Error("junction identity or coordinate is invalid");}
 return value;
}
