import test from "node:test";
import assert from "node:assert/strict";
import {CartographicAnchorKind,CartographicLabelClass,createPresentationAnchor,createCartographicLabelCandidate} from "../../../src/map/cartography/contracts.js";

test(".15.4 derived anchors are presentation identities, not geography identities",()=>{
  const anchor=createPresentationAnchor({kind:CartographicAnchorKind.DERIVED_PRESENTATION,longitude:35,latitude:-1,sourceBoundaryId:"boundary:novegeo:sovereign",sourceBoundaryVersion:2,algorithmId:"cartography:test",algorithmVersion:1});
  assert.equal(anchor.sourceGeometryId,null);
  assert.equal(anchor.kind,"DERIVED_PRESENTATION");
  assert.throws(()=>createPresentationAnchor({longitude:35,latitude:-1}),/algorithm identity/);
});

test(".15.4 label candidates preserve authoritative display name separately from rendered styling",()=>{
  const anchor=createPresentationAnchor({longitude:35,latitude:-1,algorithmId:"cartography:test",algorithmVersion:1});
  const candidate=createCartographicLabelCandidate({subjectId:"country:novegeo",displayName:"NoveGeo",labelClass:CartographicLabelClass.COUNTRY,anchor});
  assert.equal(candidate.displayName,"NoveGeo");
  assert.equal(candidate.subjectId,"country:novegeo");
});
