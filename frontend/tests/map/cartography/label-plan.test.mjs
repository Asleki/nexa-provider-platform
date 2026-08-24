import test from "node:test";
import assert from "node:assert/strict";
import {CartographicLabelClass,createCartographicLabelCandidate,createPresentationAnchor} from "../../../src/map/cartography/contracts.js";
import {createCartographicLabelPlan} from "../../../src/map/cartography/label-plan.js";

const anchor=(x,y)=>createPresentationAnchor({longitude:x,latitude:y,algorithmId:"cartography:test",algorithmVersion:1});
const candidate=(subjectId,labelClass,group=null,name="Same")=>createCartographicLabelCandidate({subjectId,displayName:name,labelClass,anchor:anchor(1,1),labelGroupReference:group});
const project=(x,y)=>({x:x*10,y:y*10});

test(".15.4 label plan deduplicates only by explicit stable group reference",()=>{
  const plan=createCartographicLabelPlan({zoom:2,project,candidates:[candidate("place:orivane",CartographicLabelClass.CITY,"naming:orivane","Orivane"),candidate("admin:orivane",CartographicLabelClass.ADMIN_CITY,"naming:orivane","Orivane")]});
  assert.equal(plan.labels.length,1);
  assert.equal(plan.labels[0].subjectId,"admin:orivane");
});

test(".15.4 same display names remain separate without grouping evidence",()=>{
  const plan=createCartographicLabelPlan({zoom:2,project,candidates:[candidate("town:a",CartographicLabelClass.TOWN,null,"Springfield"),candidate("town:b",CartographicLabelClass.TOWN,null,"Springfield")]});
  assert.equal(plan.labels.length,2);
});
