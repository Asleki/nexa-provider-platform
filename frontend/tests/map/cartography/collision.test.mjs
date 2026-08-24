import test from "node:test";
import assert from "node:assert/strict";
import {declutterCartographicLabels} from "../../../src/map/cartography/collision.js";

const style={collisionPaddingPx:2};
const item=(subjectId,priority,x)=>({label:{subjectId,priority,x,y:10,style},metrics:{width:20,height:10}});

test(".15.4 decluttering deterministically protects higher priority labels",()=>{
  const result=declutterCartographicLabels([item("low",100,11),item("high",1000,10),item("far",50,100)]);
  assert.deepEqual(result.accepted.map(x=>x.label.subjectId),["high","far"]);
  assert.equal(result.rejected[0].label.subjectId,"low");
});
