/** P006.7.11.15.3 / P006.7.11.15.10.1 — HTTP-only governed national-map client. */
import { normalizeNationalMapPayload } from "./national-map-contracts.js";
import { createGovernedSnapshotLoader } from "./governed-snapshot-loader.js";

function base(apiBaseUrl){return String(apiBaseUrl||"").replace(/\/$/,"");}
function boundsParams(bounds){
  const keys=["minLongitude","minLatitude","maxLongitude","maxLatitude"];
  for(const key of keys) if(!Number.isFinite(Number(bounds?.[key]))) throw new TypeError(`missing ${key}`);
  if(!(Number(bounds.minLongitude)<Number(bounds.maxLongitude)&&Number(bounds.minLatitude)<Number(bounds.maxLatitude))) throw new RangeError("invalid national map bounds");
  return keys.map((key)=>[key,String(Number(bounds[key]))]);
}

function selectedFamilies(families){
  return [...new Set((families||[]).map((family)=>String(family).trim().toUpperCase()).filter(Boolean))];
}

function projectSnapshot(payload, families){
  const selected=selectedFamilies(families);
  if(!selected.length) return payload;
  const allowed=new Set(selected);
  const items=Object.freeze(payload.items.filter((item)=>allowed.has(item.family)));
  return Object.freeze({
    ...payload,
    families:Object.freeze(selected),
    items,
    count:items.length,
    nextCursor:null,
    sourceSemanticChecksum:payload.semanticChecksum||null,
  });
}

export function createNationalMapClient({apiBaseUrl="",fetchRef=globalThis.fetch}={}){
  if(typeof fetchRef!=="function") throw new TypeError("fetchRef is required");
  const resolvedBase=base(apiBaseUrl);
  const loader=createGovernedSnapshotLoader({apiBaseUrl:resolvedBase,fetchRef});
  let cache=null; let etag=null;
  return Object.freeze({
    async readViewport(bounds,{families=[],limit=500,cursor=null,signal}={}){
      // P006.7.11.15.10.1: the map-first NoveGeo layer stack always requests
      // limit=2000 without a cursor. Coalesce that path into one existing
      // endpoint call with no family filter, then partition locally.
      if(!cursor&&Number(limit)===2000&&!signal){
        const normalized=normalizeNationalMapPayload(await loader.readCompleteMapViewportRaw(bounds));
        if(normalized.nextCursor) throw new Error("complete governed map snapshot exceeds single-page 2000-feature contract");
        return projectSnapshot(normalized,families);
      }

      // Preserve historical generic-client behavior for pagination, smaller
      // pages, abortable reads and non-presentation consumers.
      const params=new URLSearchParams(boundsParams(bounds));
      for(const family of families) params.append("family",family);
      params.set("limit",String(limit)); if(cursor) params.set("cursor",cursor);
      const headers={accept:"application/json"}; if(etag&&!cursor) headers["if-none-match"]=etag;
      const response=await fetchRef(`${resolvedBase}/api/v1/nngla-map/features?${params}`,{method:"GET",headers,signal});
      if(response.status===304&&cache&&!cursor) return cache;
      if(!response.ok) throw new Error(`NNGLA national map read failed (${response.status})`);
      const normalized=normalizeNationalMapPayload(await response.json());
      if(!cursor){cache=normalized; etag=response.headers?.get?.("etag")||null;}
      return normalized;
    },
  });
}
