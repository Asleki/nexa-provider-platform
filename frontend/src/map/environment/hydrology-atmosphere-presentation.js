/** Bundle 11.0B — corrected P005.3/P005.4 hydrology and atmosphere presentation. */
import { BUNDLED_WORLD_BOUNDARY_PUBLICATION } from "../presentation/publication.js";
import { createBoundaryRenderPlan } from "../presentation/boundary-render-plan.js";
import { createViewport } from "../presentation/viewport.js";
import { MapFitMode } from "../presentation/contracts.js";
import { NOVEGEO_HYDROLOGY_STANDARD } from "../hydrology/catalog.js";
import { createHydrologyRenderPlan } from "../hydrology/render-plan.js";
import { NOVEGEO_CLIMATE_STANDARD } from "../climate/catalog.js";
import { createClimateRenderPlan } from "../climate/render-plan.js";

const WIDTH=640,MIN_W=280,MIN_H=260,ASPECT=.68,Z="2";
const WATER="rgba(18,74,112,.78)";
function widthOf(c){const r=c.getBoundingClientRect?.();const m=Number(r?.width||c.clientWidth||WIDTH);return Number.isFinite(m)&&m>0?Math.max(MIN_W,m):WIDTH;}
function heightOf(w){return Math.max(MIN_H,Math.round(w*ASPECT));}
function boundaryPath(ctx,plan){ctx.beginPath();for(const p of plan.polygons)for(const ring of p.rings){ring.points.forEach((pt,i)=>i?ctx.lineTo(pt.x,pt.y):ctx.moveTo(pt.x,pt.y));ctx.closePath();}}
function clipBoundary(ctx,plan){boundaryPath(ctx,plan);ctx.clip("evenodd");}
function line(ctx,pts){ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.stroke();}
function windArrow(ctx,s){const len=5+Math.min(7,s.meanWindSpeedMps*.65);const a=(s.prevailingWindDirectionDegrees-90)*Math.PI/180;const ex=s.x+Math.cos(a)*len,ey=s.y+Math.sin(a)*len;ctx.beginPath();ctx.moveTo(s.x,s.y);ctx.lineTo(ex,ey);ctx.stroke();}
function rainfallInfluence(system,cell){
 const dx=(cell.x-system.x)/Math.max(1,system.radiusX),dy=(cell.y-system.y)/Math.max(1,system.radiusY);const angle=Math.atan2(dy,dx);const seed=Number(system.fieldModel?.shapeSeed||1);const irr=Number(system.fieldModel?.irregularity||.2);const wobble=1+irr*(.52*Math.sin(angle*3+seed*.01)+.31*Math.sin(angle*5-seed*.013)+.17*Math.cos(angle*7));const d=Math.sqrt(dx*dx+dy*dy)/Math.max(.55,wobble);return Math.max(0,1-d);
}
function rainfallColor(system,influence){const powerful=system.intensityClass==="powerful";const a=(powerful?.08:.055)+influence*(powerful?.28:.20);return powerful?`rgba(45,134,210,${a.toFixed(3)})`:`rgba(96,180,204,${a.toFixed(3)})`;}
function riverWidth(r){return r.streamOrder===3?3.2:r.streamOrder===2?2.15:1.25;}

export function renderHydrologyAtmosphereCanvas({canvas,viewport,hydrologyPlan,climatePlan,boundaryPlan}){
 const ctx=canvas?.getContext?.("2d");if(!ctx)throw new Error("environment canvas requires Canvas 2D");canvas.width=viewport.renderWidth;canvas.height=viewport.renderHeight;Object.assign(canvas.style||{},{width:`${viewport.cssWidth}px`,height:`${viewport.cssHeight}px`,position:"absolute",inset:"0",zIndex:Z,pointerEvents:"none"});ctx.setTransform(viewport.devicePixelRatio,0,0,viewport.devicePixelRatio,0,0);ctx.clearRect(0,0,viewport.cssWidth,viewport.cssHeight);
 // Surrounding water is cartographic context only. Punch sovereign land out so P005.1/P005.2 remains visible below.
 ctx.save();ctx.fillStyle=WATER;ctx.fillRect(0,0,viewport.cssWidth,viewport.cssHeight);ctx.globalCompositeOperation="destination-out";boundaryPath(ctx,boundaryPlan);ctx.fill("evenodd");ctx.restore();
 ctx.save();clipBoundary(ctx,boundaryPlan);
 // Baseline climate tint stays subordinate to terrain.
 for(const c of climatePlan.cells){ctx.fillStyle=c.color;ctx.fillRect(c.x-climatePlan.cellWidth/2,c.y-climatePlan.cellHeight/2,climatePlan.cellWidth,climatePlan.cellHeight);}
 // Two governed rainfall systems render as irregular intensity fields; their radius boundary is intentionally invisible.
 for(const s of climatePlan.rainfallSystems){for(const c of climatePlan.cells){const influence=rainfallInfluence(s,c);if(influence<=.08)continue;ctx.fillStyle=rainfallColor(s,influence);ctx.beginPath();ctx.arc(c.x,c.y,Math.max(climatePlan.cellWidth,climatePlan.cellHeight)*(.55+.7*influence),0,Math.PI*2);ctx.fill();}}
 // Restrained wind marks.
 ctx.save();ctx.strokeStyle="rgba(225,239,246,.36)";ctx.lineWidth=.9;for(const w of climatePlan.winds)windArrow(ctx,w);ctx.restore();
 // Lakes are water bodies, not point markers.
 ctx.fillStyle="rgba(32,132,197,.90)";for(const lake of hydrologyPlan.lakes)for(const ring of lake.rings){ctx.beginPath();ring.forEach((p,i)=>i?ctx.lineTo(p.x,p.y):ctx.moveTo(p.x,p.y));ctx.closePath();ctx.fill();}
 // Rivers preserve hierarchy: tributaries thin, principal channels widest.
 ctx.strokeStyle="rgba(58,168,226,.94)";ctx.lineCap="round";ctx.lineJoin="round";for(const river of [...hydrologyPlan.rivers].sort((a,b)=>a.streamOrder-b.streamOrder)){ctx.lineWidth=riverWidth(river);line(ctx,river.points);}ctx.restore();
 return Object.freeze({status:"RENDERED",hydrologyDatasetId:hydrologyPlan.datasetId,riverCount:hydrologyPlan.rivers.length,lakeCount:hydrologyPlan.lakes.length,climateDatasetId:climatePlan.datasetId,climateSampleCount:climatePlan.cells.length,rainfallSystemCount:climatePlan.rainfallSystems.length,surroundingWaterContext:true,rainfallPresentation:"irregular_intensity_field"});
}
export function mountHydrologyAtmospherePresentation(documentRef,{hydrologyPublication=NOVEGEO_HYDROLOGY_STANDARD,climatePublication=NOVEGEO_CLIMATE_STANDARD,boundaryPublication=BUNDLED_WORLD_BOUNDARY_PUBLICATION,devicePixelRatio=Number(globalThis.devicePixelRatio||1)}={}){
 const container=documentRef?.querySelector?.("[data-role='future-map-viewport']");if(!container||typeof documentRef?.createElement!=="function")return Object.freeze({status:"UNAVAILABLE",reason:"viewport_missing"});const boundaryCanvas=container.querySelector?.("[data-role='novegeo-map-canvas']");if(!boundaryCanvas)return Object.freeze({status:"UNAVAILABLE",reason:"boundary_canvas_missing"});const w=widthOf(container),h=heightOf(w);const viewport=createViewport({cssWidth:w,cssHeight:h,devicePixelRatio,padding:Math.min(36,Math.max(20,w*.055)),fitMode:MapFitMode.BOUNDARY,extent:boundaryPublication.extent});const hp=createHydrologyRenderPlan(hydrologyPublication,viewport),cp=createClimateRenderPlan(climatePublication,viewport),bp=createBoundaryRenderPlan(boundaryPublication,viewport);const existing=container.querySelector?.("[data-role='novegeo-hydrology-atmosphere-canvas']");const canvas=existing||documentRef.createElement("canvas");canvas.setAttribute("data-role","novegeo-hydrology-atmosphere-canvas");canvas.setAttribute("aria-hidden","true");if(container.style)container.style.position="relative";if(!existing){const coord=container.querySelector?.("[data-role='novegeo-full-viewport-coordinate-canvas']");if(coord&&container.insertBefore)container.insertBefore(canvas,coord);else container.appendChild?.(canvas);}return renderHydrologyAtmosphereCanvas({canvas,viewport,hydrologyPlan:hp,climatePlan:cp,boundaryPlan:bp});
}
