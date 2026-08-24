import test from "node:test";
import assert from "node:assert/strict";
import {deriveCountryLabelAnchor,createNoveGeoCountryLabelCandidate} from "../../../src/map/cartography/country-anchor.js";

const boundary=Object.freeze({
  boundaryId:"boundary:novegeo:sovereign",boundaryVersion:2,publicationId:"publication:novegeo:world-boundary:v2",
  coordinateReference:Object.freeze({coordinateReferenceId:"crs:novegeo:geographic",version:1,axisOrder:Object.freeze(["longitude","latitude"])}),
  extent:Object.freeze({minLongitude:0,minLatitude:0,maxLongitude:21,maxLatitude:10}),
  geometry:Object.freeze({type:"MultiPolygon",coordinates:Object.freeze([
    Object.freeze([Object.freeze([[0,0],[10,0],[10,10],[0,10],[0,0]])]),
    Object.freeze([Object.freeze([[20,0],[21,0],[21,1],[20,1],[20,0]])]),
  ])}),
});

test(".15.4 derives deterministic country label anchor from largest sovereign polygon",()=>{
  const a=deriveCountryLabelAnchor(boundary);const b=deriveCountryLabelAnchor(boundary);
  assert.deepEqual(a,b);
  assert.equal(a.sourceBoundaryVersion,2);
  assert.ok(a.longitude>2&&a.longitude<8);
  assert.ok(a.latitude>2&&a.latitude<8);
});

test(".15.4 NoveGeo country candidate keeps country identity and publication provenance",()=>{
  const c=createNoveGeoCountryLabelCandidate(boundary);
  assert.equal(c.subjectId,"country:novegeo");
  assert.equal(c.displayName,"NoveGeo");
  assert.equal(c.publicationReference,"publication:novegeo:world-boundary:v2");
  assert.equal(c.labelGroupReference,"country:novegeo");
});
