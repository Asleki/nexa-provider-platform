import test from "node:test";
import assert from "node:assert/strict";
import {CartographicLabelClass} from "../../../src/map/cartography/contracts.js";
import {resolveCartographicStyle,renderCartographicText} from "../../../src/map/cartography/style-catalog.js";

test(".15.4 country style produces presentation uppercase without mutating source name",()=>{
  const style=resolveCartographicStyle(CartographicLabelClass.COUNTRY,1);
  assert.equal(style.eligible,true);
  assert.equal(renderCartographicText("NoveGeo",style),"NOVEGEO");
});

test(".15.4 country label yields to local detail at deep zoom",()=>{
  assert.equal(resolveCartographicStyle(CartographicLabelClass.COUNTRY,5).eligible,false);
  assert.equal(resolveCartographicStyle(CartographicLabelClass.CITY,5).eligible,true);
});
