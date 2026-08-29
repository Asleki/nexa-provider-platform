import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import vm from "node:vm";

const ROOT=resolve(dirname(fileURLToPath(import.meta.url)),"../..");
const cachePolicy=readFileSync(resolve(ROOT,"src/pwa/cache-policy.js"),"utf8");
const serviceWorker=readFileSync(resolve(ROOT,"sw.js"),"utf8");
const cityAssets=["./src/app/features/novegeo-city-map-experience.js","./src/map/cartography/city-anchor.js","./src/map/cartography/city-cartographic-overlay.js"];
function quotedAssets(source){return [...source.matchAll(/^\s*[\"'](\.\/[^\"']+)[\"'],?\s*$/gm)].map(m=>m[1]);}

test(".15.7 preserves v17 and mirrors all additive CITY assets",()=>{
  assert.match(cachePolicy,/PWA_CACHE_VERSION\s*=\s*[\"']nexilabs-shell-v17[\"']/); assert.match(serviceWorker,/CACHE_NAME\s*=\s*[\"']nexilabs-shell-v17[\"']/);
  for(const asset of cityAssets){assert.ok(quotedAssets(cachePolicy).includes(asset));assert.ok(quotedAssets(serviceWorker).includes(asset));}
  assert.deepEqual(quotedAssets(serviceWorker),quotedAssets(cachePolicy));
  assert.equal(new Set(quotedAssets(cachePolicy)).size,quotedAssets(cachePolicy).length);
});

test(".15.7 preserves historical refresh markers and appends CITY marker",()=>{
  assert.match(serviceWorker,/nexilabs-refresh-p006-7-11-15-4-r2/);
  assert.match(serviceWorker,/nexilabs-refresh-p006-7-11-15-6-r1/);
  assert.match(serviceWorker,/CITY_SAME_GENERATION_REFRESH_MARKER = "nexilabs-refresh-p006-7-11-15-7-r1"/);
});

function makeWorkerHarness(initialCacheNames=[]){const listeners=new Map();const stores=new Map(initialCacheNames.map(n=>[n,new Map()]));const navigations=[];let claimed=0,skipped=0;function cacheObject(name){if(!stores.has(name))stores.set(name,new Map());const content=stores.get(name);return {async addAll(assets){for(const asset of assets)content.set(asset,{asset,clone(){return this;}});},async put(asset,response){content.set(asset,response);},async match(asset){return content.get(typeof asset==="string"?asset:asset.url);}};}const caches={async open(name){return cacheObject(name);},async keys(){return [...stores.keys()];},async delete(name){return stores.delete(name);},async match(request){const key=typeof request==="string"?request:request.url;for(const content of stores.values())if(content.has(key))return content.get(key);}};const self={location:{origin:"http://127.0.0.1:8765"},addEventListener(type,listener){listeners.set(type,listener);},async skipWaiting(){skipped+=1;},clients:{async claim(){claimed+=1;},async matchAll(){return [{url:"http://127.0.0.1:8765/#/simulation/novegeo",async navigate(url){navigations.push(url);}},{url:"https://external.example/",async navigate(url){navigations.push(url);}}];}}};vm.runInNewContext(serviceWorker,{self,caches,URL,AbortController,setTimeout,clearTimeout,fetch:async()=>{throw new Error("network not expected");}});async function run(type){let promise;listeners.get(type)({waitUntil(value){promise=value;}});await promise;}return {stores,navigations,run,get claimed(){return claimed;},get skipped(){return skipped;}};}

test("existing v17 receives CITY same-generation refresh without losing older markers",async()=>{const h=makeWorkerHarness(["nexilabs-shell-v17"]);await h.run("install");assert.equal(h.skipped,1);for(const marker of ["nexilabs-refresh-p006-7-11-15-4-r2","nexilabs-refresh-p006-7-11-15-6-r1","nexilabs-refresh-p006-7-11-15-7-r1"])assert.ok(h.stores.has(marker));await h.run("activate");assert.equal(h.claimed,1);assert.deepEqual(h.navigations,["http://127.0.0.1:8765/#/simulation/novegeo"]);});
