/** P005.4 pure climate/rainfall/wind viewport render plan. */
import { geographicToViewport } from "../presentation/viewport.js";
import { validateClimatePublication, climateColorForRainfall } from "./contracts.js";
export function createClimateRenderPlan(publication,viewport){
 const value=validateClimatePublication(publication);
 const sampleStep=0.84;
 const p0=geographicToViewport(value.extent.minLongitude,value.extent.maxLatitude,viewport);
 const px=geographicToViewport(value.extent.minLongitude+sampleStep,value.extent.maxLatitude,viewport);
 const py=geographicToViewport(value.extent.minLongitude,value.extent.maxLatitude-sampleStep,viewport);
 const cells=value.samples.map(s=>{ const p=geographicToViewport(s.longitude,s.latitude,viewport); return Object.freeze({...s,x:p.x,y:p.y,color:climateColorForRainfall(s.annualRainfallMm)}); });
 const rainfallSystems=value.rainfallSystems.map(s=>{ const c=geographicToViewport(s.center.longitude,s.center.latitude,viewport); const rx=Math.abs(geographicToViewport(s.center.longitude+s.radiusLongitudeDegrees,s.center.latitude,viewport).x-c.x); const ry=Math.abs(geographicToViewport(s.center.longitude,s.center.latitude+s.radiusLatitudeDegrees,viewport).y-c.y); return Object.freeze({...s,x:c.x,y:c.y,radiusX:rx,radiusY:ry}); });
 const winds=cells.filter((_,i)=>i%9===0);
 return Object.freeze({datasetId:value.datasetId,datasetVersion:value.datasetVersion,cellWidth:Math.abs(px.x-p0.x),cellHeight:Math.abs(py.y-p0.y),cells:Object.freeze(cells),rainfallSystems:Object.freeze(rainfallSystems),winds:Object.freeze(winds)});
}
