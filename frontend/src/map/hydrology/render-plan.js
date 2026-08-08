/** P005.3 pure hydrology-to-viewport render plan. */
import { geographicToViewport } from "../presentation/viewport.js";
import { validateHydrologyPublication } from "./contracts.js";
export function createHydrologyRenderPlan(publication,viewport){
 const value=validateHydrologyPublication(publication);
 const rivers=value.rivers.map(r=>Object.freeze({riverId:r.riverId,riverClass:r.riverClass,streamOrder:r.streamOrder,referencePoint:Object.freeze({...r.referencePoint}),downstreamJunctionId:r.downstreamJunctionId??null,downstreamRiverId:r.downstreamRiverId??null,points:Object.freeze(r.geometry.coordinates.map(([lon,lat])=>geographicToViewport(lon,lat,viewport)))}));
 const lakes=value.lakes.map(l=>Object.freeze({lakeId:l.lakeId,referencePoint:Object.freeze({...l.referencePoint}),hydrologicRole:l.hydrologicRole,rings:Object.freeze(l.geometry.coordinates.map(ring=>Object.freeze(ring.map(([lon,lat])=>geographicToViewport(lon,lat,viewport)))))}));
 const junctions=value.junctions.map(j=>{const p=geographicToViewport(j.coordinate.longitude,j.coordinate.latitude,viewport);return Object.freeze({junctionId:j.junctionId,junctionType:j.junctionType,receivingRiverId:j.receivingRiverId,incomingRiverIds:Object.freeze([...j.incomingRiverIds]),longitude:j.coordinate.longitude,latitude:j.coordinate.latitude,x:p.x,y:p.y})});
 return Object.freeze({datasetId:value.datasetId,datasetVersion:value.datasetVersion,rivers:Object.freeze(rivers),lakes:Object.freeze(lakes),junctions:Object.freeze(junctions)});
}
