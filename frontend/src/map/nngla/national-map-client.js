/** P006.7.11.15.3 — HTTP-only governed national-map client. */
import { normalizeNationalMapPayload } from "./national-map-contracts.js";
function base(apiBaseUrl){return String(apiBaseUrl||"").replace(/\/$/,"");}
function boundsParams(bounds){
  const keys=["minLongitude","minLatitude","maxLongitude","maxLatitude"];
  for(const key of keys) if(!Number.isFinite(Number(bounds?.[key]))) throw new TypeError(`missing ${key}`);
  if(!(Number(bounds.minLongitude)<Number(bounds.maxLongitude)&&Number(bounds.minLatitude)<Number(bounds.maxLatitude))) throw new RangeError("invalid national map bounds");
  return keys.map((key)=>[key,String(Number(bounds[key]))]);
}
export function createNationalMapClient({apiBaseUrl="",fetchRef=globalThis.fetch}={}){
  if(typeof fetchRef!=="function") throw new TypeError("fetchRef is required");
  let cache=null; let etag=null;
  return Object.freeze({
    async readViewport(bounds,{families=[],limit=500,cursor=null,signal}={}){
      const params=new URLSearchParams(boundsParams(bounds));
      for(const family of families) params.append("family",family);
      params.set("limit",String(limit)); if(cursor) params.set("cursor",cursor);
      const headers={accept:"application/json"}; if(etag&&!cursor) headers["if-none-match"]=etag;
      const response=await fetchRef(`${base(apiBaseUrl)}/api/v1/nngla-map/features?${params}`,{method:"GET",headers,signal});
      if(response.status===304&&cache&&!cursor) return cache;
      if(!response.ok) throw new Error(`NNGLA national map read failed (${response.status})`);
      const normalized=normalizeNationalMapPayload(await response.json());
      if(!cursor){cache=normalized; etag=response.headers?.get?.("etag")||null;}
      return normalized;
    },
  });
}
