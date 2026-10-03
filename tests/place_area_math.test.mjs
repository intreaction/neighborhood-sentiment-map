import test from 'node:test';
import assert from 'node:assert/strict';
import {areaAt,areaColor,areaValue,formatAreaValue,FOCUSES} from '../src/place_area_math.mjs';
test('map selection respects polygon holes and multipart areas',()=>{
 const ring=[[0,0],[4,0],[4,4],[0,4],[0,0]],hole=[[1,1],[2,1],[2,2],[1,2],[1,1]];
 const features=[{properties:{zip:'a'},geometry:{type:'Polygon',coordinates:[ring,hole]}},{properties:{zip:'b'},geometry:{type:'MultiPolygon',coordinates:[[[[5,0],[6,0],[6,1],[5,1],[5,0]]]]}}];
 assert.equal(areaAt([.5,.5],features),'a');assert.equal(areaAt([1.5,1.5],features),null);assert.equal(areaAt([5.5,.5],features),'b');assert.equal(areaAt([20,20],features),null);
});
test('low income, declining activity and relative deterioration map to the warm end',()=>{
 assert.equal(areaColor(20000,'income'),'rgb(153,53,37)');
 assert.equal(areaColor(-100,'decline'),'rgb(177,58,36)');
 assert.equal(areaColor(-.15,'experience'),'rgb(177,58,36)');
 assert.equal(areaColor(.15,'experience'),'rgb(35,118,122)');
 assert.equal(areaColor(0,'experience'),'rgb(248,239,212)');
});
test('zero observations and missing estimates remain distinguishable',()=>{
 assert.equal(areaValue({access_share_pct:0},'access'),0);
 assert.equal(areaValue({access_share_pct:null},'access'),null);
 assert.equal(formatAreaValue(0,'access'),'0.0%');
 assert.equal(formatAreaValue(null,'access'),'Limited data');
 assert.notEqual(areaColor(null,'access'),areaColor(0,'access'));
 for(const f of Object.keys(FOCUSES).filter(f=>f!=='none'))assert.equal(areaValue({},f),null);
});

test('stable ZIP anchors stay inside every shipped boundary, including holes',async()=>{
 const {areaAnchor}=await import('../src/place_area_math.mjs');
 const {readFileSync}=await import('node:fs');
 const map=JSON.parse(readFileSync(new URL('../web/place-map.json',import.meta.url)));
 for(const city of map.cities)for(const feature of city.features){
  const anchor=areaAnchor(feature);
  assert.equal(areaAt(anchor,[feature]),feature.properties.zip);
  assert.deepEqual(areaAnchor(feature),anchor);
 }
 const ring=[[0,0],[8,0],[8,8],[0,8],[0,0]],hole=[[2,2],[6,2],[6,6],[2,6],[2,2]];
 const feature={properties:{zip:'hole'},geometry:{type:'Polygon',coordinates:[ring,hole]}};
 assert.equal(areaAt(areaAnchor(feature),[feature]),'hole');
});

test('combined categories preserve both signals and explicit boundary rules',()=>{
 const cases=[[19.9,0,0],[0,-1,1],[20,1,2],[20,-.01,3]];
 for(const [poverty_pct,growth_pct,category] of cases)assert.equal(areaValue({poverty_pct,growth_pct},'combined'),category);
 assert.equal(new Set(cases.map(([, ,category])=>areaColor(category,'combined'))).size,4);
 assert.equal(formatAreaValue(3,'combined'),'Higher poverty · declining');
 for(const row of [{poverty_pct:null,growth_pct:-5},{poverty_pct:25,growth_pct:null},{poverty_pct:NaN,growth_pct:0},{}])assert.equal(areaValue(row,'combined'),null);
 assert.equal(areaValue({poverty_pct:0,growth_pct:0},'combined'),0);
 assert.notEqual(areaColor(null,'combined'),areaColor(0,'combined'));
});
