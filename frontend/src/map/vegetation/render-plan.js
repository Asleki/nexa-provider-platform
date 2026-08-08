/** P005.5 vegetation/aridity viewport render plan. */
import { geographicToViewport } from "../presentation/viewport.js";
import { validateVegetationPublication,vegetationColorForClass } from "./contracts.js";
export function createVegetationRenderPlan(publication,viewport){
 const value=validateVegetationPublication(publication);const step=.84;
 const p0=geographicToViewport(value.extent.minLongitude,value.extent.maxLatitude,viewport),px=geographicToViewport(value.extent.minLongitude+step,value.extent.maxLatitude,viewport),py=geographicToViewport(value.extent.minLongitude,value.extent.maxLatitude-step,viewport);
 const cells=value.samples.map(s=>{const p=geographicToViewport(s.longitude,s.latitude,viewport);return Object.freeze({...s,x:p.x,y:p.y,color:vegetationColorForClass(s.vegetationClass)});});
 return Object.freeze({datasetId:value.datasetId,datasetVersion:value.datasetVersion,cellWidth:Math.abs(px.x-p0.x),cellHeight:Math.abs(py.y-p0.y),cells:Object.freeze(cells)});
}
