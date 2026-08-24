/** P006.7.11.15.3 — fail-closed in-memory national geography state. */
export const NationalMapStateStatus=Object.freeze({IDLE:"IDLE",LOADING:"LOADING",READY:"READY",PUBLICATION_PENDING:"PUBLICATION_PENDING",DEGRADED:"DEGRADED",DISCONNECTED:"DISCONNECTED"});
const HYDROLOGY=new Set(["RIVER","LAKE","STREAM","WETLAND","RESERVOIR"]);
const LANDFORM=new Set(["MOUNTAIN","VALLEY","PLAIN","PLATEAU","HILL","ESCARPMENT"]);
export function createNationalMapState(){
  let snapshot=Object.freeze({status:NationalMapStateStatus.IDLE,items:Object.freeze([]),layerAvailability:Object.freeze({places:false,roads:false,administrativeBoundaries:false,hydrology:false,landforms:false}),error:null});
  const publish=(next)=>snapshot=Object.freeze(next);
  return Object.freeze({
    get snapshot(){return snapshot;},
    loading(){publish({...snapshot,status:NationalMapStateStatus.LOADING,error:null});return snapshot;},
    apply(payload){
      const items=Object.freeze([...(payload?.items||[])]); const availability={places:false,roads:false,administrativeBoundaries:false,hydrology:false,landforms:false};
      for(const item of items){
        if(item.family==="PLACE") availability.places=true;
        if(item.family==="ROAD") availability.roads=true;
        if(item.family==="ADMINISTRATIVE_AREA") availability.administrativeBoundaries=true;
        if(item.family==="GEOGRAPHIC_FEATURE"){const code=String(item.classificationCode||"").toUpperCase(); if(HYDROLOGY.has(code)) availability.hydrology=true; if(LANDFORM.has(code)) availability.landforms=true;}
      }
      publish({status:items.length?NationalMapStateStatus.READY:NationalMapStateStatus.PUBLICATION_PENDING,items,layerAvailability:Object.freeze(availability),error:null,readRuntime:payload?.readRuntime||null,mapReadModelVersion:payload?.mapReadModelVersion||1,semanticChecksum:payload?.semanticChecksum||null}); return snapshot;
    },
    degraded(error){publish({...snapshot,status:NationalMapStateStatus.DEGRADED,items:Object.freeze([]),error:error?.message||String(error)});return snapshot;},
    disconnect(){publish({...snapshot,status:NationalMapStateStatus.DISCONNECTED,items:Object.freeze([])});return snapshot;},
  });
}
