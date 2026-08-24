import test from "node:test";
import assert from "node:assert/strict";
import {renderCartographicLabels} from "../../../src/map/cartography/label-renderer.js";

function context(){const calls=[];return {calls,font:"",save(){},restore(){},measureText(t){return {width:t.length*8};},strokeText(t,x,y){calls.push(["stroke",t,x,y]);},fillText(t,x,y){calls.push(["fill",t,x,y]);}};}
const style={priority:1000,resolvedFontSizePx:20,fontWeight:800,fontFamily:"system-ui",letterSpacingPx:2,collisionPaddingPx:4,haloWidthPx:4,haloStyle:"black",fillStyle:"white"};

test(".15.4 renderer draws halo and fill for an accepted country label",()=>{
  const ctx=context();
  const receipt=renderCartographicLabels({context:ctx,plan:{planId:"p",planVersion:1,labels:[{subjectId:"country:novegeo",priority:1000,x:100,y:60,renderedText:"NOVEGEO",style}]}});
  assert.equal(receipt.renderedCount,1);
  assert.equal(ctx.calls.filter(c=>c[0]==="stroke").length,7);
  assert.equal(ctx.calls.filter(c=>c[0]==="fill").length,7);
});
