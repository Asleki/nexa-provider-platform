import test from "node:test";
import assert from "node:assert/strict";
import {installNoveGeoNationalGeographyExperience} from "../../../src/app/features/novegeo-national-geography-experience.js";

function documentRef(){
  const page={dataset:{}};
  const status={dataset:{},setAttribute(name,value){if(name==="data-role")this.role=value;}};
  const section={children:[],querySelector(selector){return selector.includes("novegeo-national-geography-consumer-status")?this.children.find((x)=>x.role==="novegeo-national-geography-consumer-status")||null:null;},append(node){this.children.push(node);}};
  return {
    page,section,status,
    createElement(){return {dataset:{},setAttribute(name,value){if(name==="data-role")this.role=value;}};},
    querySelector(selector){
      if(selector===".novegeo-feature-page") return page;
      if(selector==="[data-role='novegeo-national-layer-status']") return section;
      return null;
    },
  };
}

test("Bundle 22B experience consumes the sovereign extent then map API and keeps zero-public state pending",async()=>{
  const doc=documentRef();
  const win={location:{protocol:"http:",hostname:"127.0.0.1"},addEventListener(){},removeEventListener(){}};
  const boundary={extent:{minLongitude:30,minLatitude:-20,maxLongitude:32,maxLatitude:-17}};
  const exp=installNoveGeoNationalGeographyExperience({
    documentRef:doc,windowRef:win,fetchRef:()=>{},apiBaseUrl:"http://127.0.0.1:8000",
    createBoundaryClientRef:()=>({getActive:async()=>boundary}),
    createMapClientRef:()=>({readViewport:async()=>({items:[],readRuntime:"simulation",mapReadModelVersion:1,semanticChecksum:"x"})}),
  });
  const result=await exp.refresh();
  assert.equal(result.status,"PUBLICATION_PENDING");
  assert.equal(doc.page.dataset.nationalGeographyCount,"0");
  assert.equal(doc.section.children[0].textContent,"Live national geography connected · no published map features yet");
  exp.disconnect();
});
