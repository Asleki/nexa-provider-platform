/** P006.7.11.15.3 — additive PWA consumer for PUBLIC national NNGLA geography. */
import { resolveLiveApiBaseUrl } from "../../config/live-api-endpoint.js";
import { createLiveWorldBoundaryClient } from "../../map/geography/live-boundary-client.js";
import { createNationalMapClient } from "../../map/nngla/national-map-client.js";
import { createNationalMapState,NationalMapStateStatus } from "../../map/nngla/national-map-state.js";

function updateLayerStatus(documentRef,availability){
  for(const [key,available] of Object.entries(availability||{})){
    const node=documentRef.querySelector?.(`[data-national-layer-key='${key}'] [data-layer-availability]`);
    if(!node) continue; node.dataset.layerAvailability=available?"AVAILABLE":"PUBLICATION_PENDING"; node.textContent=available?"Available":"Publication pending";
  }
}
function consumerStatusText(snapshot){
  if(snapshot.status===NationalMapStateStatus.LOADING) return "Loading live published national geography…";
  if(snapshot.status===NationalMapStateStatus.READY) return `Live published national geography · ${snapshot.items?.length||0} map features`;
  if(snapshot.status===NationalMapStateStatus.PUBLICATION_PENDING) return "Live national geography connected · no published map features yet";
  if(snapshot.status===NationalMapStateStatus.DEGRADED) return "Live national geography unavailable · no bundled national authority substituted";
  if(snapshot.status===NationalMapStateStatus.DISCONNECTED) return "Live national geography disconnected";
  return "Live national geography awaiting activation";
}
function updateConsumerStatus(documentRef,snapshot){
  const section=documentRef.querySelector?.("[data-role='novegeo-national-layer-status']");
  if(!section||typeof documentRef.createElement!=="function") return;
  let node=section.querySelector?.("[data-role='novegeo-national-geography-consumer-status']");
  if(!node){node=documentRef.createElement("p");node.className="novegeo-national-search-reservation";node.dataset.novegeoNationalGeographyConsumerStatus="true";node.setAttribute?.("data-role","novegeo-national-geography-consumer-status");section.append?.(node);}
  node.dataset.status=snapshot.status;node.textContent=consumerStatusText(snapshot);
}
function updatePageState(documentRef,snapshot){
  const page=documentRef.querySelector?.(".novegeo-feature-page"); if(!page) return; page.dataset.nationalGeographyStatus=snapshot.status; page.dataset.nationalGeographyCount=String(snapshot.items?.length||0);
  updateLayerStatus(documentRef,snapshot.layerAvailability);updateConsumerStatus(documentRef,snapshot);
}
export function installNoveGeoNationalGeographyExperience({documentRef=globalThis.document,windowRef=globalThis.window,fetchRef=globalThis.fetch,apiBaseUrl="",createBoundaryClientRef=createLiveWorldBoundaryClient,createMapClientRef=createNationalMapClient}={}){
  const state=createNationalMapState(); let generation=0; let disconnected=false; let inFlight=null;
  const runRefresh=async()=>{
    const page=documentRef.querySelector?.(".novegeo-feature-page"); if(!page) return Object.freeze({status:"INACTIVE"});
    const resolved=resolveLiveApiBaseUrl({apiBaseUrl,windowRef}); if(!resolved){state.degraded(new Error("live_api_endpoint_unavailable"));updatePageState(documentRef,state.snapshot);return state.snapshot;}
    const token=++generation; state.loading(); updatePageState(documentRef,state.snapshot);
    try{
      const boundary=await createBoundaryClientRef({apiBaseUrl:resolved,fetchRef}).getActive(); if(disconnected||token!==generation) return Object.freeze({status:"DISCONNECTED"});
      const extent=boundary.extent; const client=createMapClientRef({apiBaseUrl:resolved,fetchRef});
      const payload=await client.readViewport({minLongitude:extent.minLongitude,minLatitude:extent.minLatitude,maxLongitude:extent.maxLongitude,maxLatitude:extent.maxLatitude},{families:["PLACE","ADMINISTRATIVE_AREA","ROAD","GEOGRAPHIC_FEATURE"],limit:2000});
      if(disconnected||token!==generation) return Object.freeze({status:"DISCONNECTED"}); state.apply(payload); updatePageState(documentRef,state.snapshot); return state.snapshot;
    }catch(error){if(!disconnected){state.degraded(error);updatePageState(documentRef,state.snapshot);}return state.snapshot;}
  };
  const refresh=()=>{
    if(disconnected) return Promise.resolve(Object.freeze({status:"DISCONNECTED"}));
    if(inFlight) return inFlight;
    inFlight=runRefresh().finally(()=>{inFlight=null;});
    return inFlight;
  };
  const onRoute=()=>queueMicrotask(()=>{if(documentRef.querySelector?.(".novegeo-feature-page")) void refresh();});
  windowRef?.addEventListener?.("hashchange",onRoute); onRoute();
  return Object.freeze({status:NationalMapStateStatus.IDLE,state,refresh,disconnect(){disconnected=true;generation++;windowRef?.removeEventListener?.("hashchange",onRoute);state.disconnect();}});
}
