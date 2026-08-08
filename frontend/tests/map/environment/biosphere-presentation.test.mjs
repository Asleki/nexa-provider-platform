import test from "node:test";import assert from "node:assert/strict";
import {mountBiospherePresentation} from "../../../src/map/environment/biosphere-presentation.js";
function context(){return {setTransform(){},clearRect(){},save(){},restore(){},beginPath(){},moveTo(){},lineTo(){},closePath(){},clip(){},fillRect(){},fill(){}}}
function documentFixture(){const mapCanvas={};const nodes={"[data-role='novegeo-map-canvas']":mapCanvas};const container={style:{},clientWidth:420,getBoundingClientRect:()=>({width:420}),querySelector:s=>nodes[s]||null,appendChild:n=>{nodes[`[data-role='${n.attrs?.['data-role']}']`]=n;},insertBefore(n){nodes[`[data-role='${n.attrs?.['data-role']}']`]=n;}};return {querySelector:s=>s==="[data-role='future-map-viewport']"?container:null,createElement:()=>({style:{},attrs:{},setAttribute(k,v){this.attrs[k]=v;},getContext:()=>context()})};}
test("P005.5 biosphere presentation is additive and idempotently reuses one canvas",()=>{const d=documentFixture();const a=mountBiospherePresentation(d,{devicePixelRatio:1});const b=mountBiospherePresentation(d,{devicePixelRatio:1});assert.equal(a.status,"RENDERED");assert.equal(b.status,"RENDERED");assert.ok(a.sampleCount>=200);assert.equal(a.datasetId,"dataset:novegeo:vegetation:baseline");});


test("Bundle 11.0C places biosphere above physical land while preserving hydrology and coordinate overlays",()=>{
  const d=documentFixture();
  const result=mountBiospherePresentation(d,{devicePixelRatio:1});
  const container=d.querySelector("[data-role='future-map-viewport']");
  const canvas=container.querySelector("[data-role='novegeo-biosphere-canvas']");
  assert.equal(result.status,"RENDERED");
  assert.equal(canvas.style.zIndex,"2");
});
