/** P006.7.11.15.3 — browser contracts for governed national geography. */
export const NATIONAL_MAP_FAMILIES=Object.freeze(["PLACE","ADMINISTRATIVE_AREA","ROAD","GEOGRAPHIC_FEATURE"]);
export function normalizeNationalMapPayload(payload){
  if(!payload||payload.authorityId!=="authority:nngla"||payload.countryId!=="country:novegeo") throw new TypeError("invalid NNGLA map authority payload");
  if(!["simulation","production"].includes(payload.readRuntime)) throw new TypeError("invalid NNGLA map runtime");
  if(!Array.isArray(payload.items)) throw new TypeError("NNGLA map items must be an array");
  const items=payload.items.map((item)=>{
    if(!item||!NATIONAL_MAP_FAMILIES.includes(item.family)||!item.subjectId||!item.publicationReference) throw new TypeError("invalid published NNGLA map item");
    if(item.publicEligible!==true||item.mapRenderable!==true) throw new TypeError("map API returned non-public or non-renderable item");
    if(!item.geometryId||!Number.isInteger(item.geometryVersion)||item.geometryVersion<1) throw new TypeError("invalid NNGLA geometry identity/version");
    if(item.crsCode!=="NG-CRS-EPSG4326"||!item.geometry||typeof item.geometry!=="object") throw new TypeError("invalid NNGLA map geometry");
    return Object.freeze({...item,geometry:Object.freeze(item.geometry)});
  });
  return Object.freeze({...payload,items:Object.freeze(items)});
}
