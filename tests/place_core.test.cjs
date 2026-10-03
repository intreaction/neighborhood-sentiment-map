const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {distanceMeters,placeProfile,updateProposal,inspectProposal,selectMapPoint,parseCommand} = require('../src/place_core.cjs');
const {projectEstimate} = require('../src/project_model_math.js');
const data = JSON.parse(fs.readFileSync(path.join(__dirname,'../web/place-data.json'),'utf8'));
const model = JSON.parse(fs.readFileSync(path.join(__dirname,'../data/derived/project_model.json'),'utf8'));
const initial = {city:'Tucson',longitude:-110.97,latitude:32.22,project_type:'Civic park',cost_millions:25,project_id:null};
const located = id => updateProposal(initial,{project_id:id},data);

test('ZIP samples without reviews allow scenario edits while point placement remains guarded',()=>{
  const fixture={cities:[{id:'test',bounds:[-1,-1,1,1],businesses:[]}]};
  const state={...initial,city:'test',longitude:0,latitude:0};
  assert.throws(()=>updateProposal(state,{cost_millions:50},fixture),/Placement requires/);
  const next=updateProposal(state,{cost_millions:50},fixture,{allowEmptyProfile:true});
  assert.equal(next.cost_millions,50);
  assert.equal(placeProfile(fixture,next).baseline_reviewed,0);
  assert.throws(()=>updateProposal(state,{longitude:5,latitude:5},fixture,{allowEmptyProfile:true}),/coverage/);
});

test('500 m boundary includes the boundary and excludes a point beyond it',()=>{
  const latitudeFor = meters => meters/6371008.8*180/Math.PI;
  const fixture = {baseline_years:[2018,2019],cities:[{id:'test',bounds:[-1,-1,1,1],businesses:[
    [0,0,0],[0,latitudeFor(499),8],[0,latitudeFor(500),12],[0,latitudeFor(501),100]
  ]}]};
  assert.equal(distanceMeters([0,0],[0,latitudeFor(500)]),500);
  const profile=placeProfile(fixture,{city:'test',longitude:0,latitude:0});
  assert.equal(profile.inventoried_businesses,3);
  assert.equal(profile.baseline_reviewed,2);
  assert.equal(profile.reviews,20);
  assert.equal(profile.pre_reviews_per_business,10);
});

test('zero baseline observations stay distinct from unavailable geographic coverage',()=>{
  const fixture={baseline_years:[2018,2019],cities:[{id:'test',bounds:[0,0,1,1],businesses:[[.5,.5,0]]}]};
  const zero=placeProfile(fixture,{city:'test',longitude:.5,latitude:.5});
  assert.equal(zero.status,'no_reviews');
  assert.equal(zero.inventoried_businesses,1);
  assert.equal(zero.baseline_reviewed,0);
  assert.equal(zero.reviews,0);
  assert.equal(zero.pre_reviews_per_business,null);
  const empty=placeProfile(fixture,{city:'test',longitude:.1,latitude:.1});
  assert.equal(empty.inventoried_businesses,0);
  assert.equal(empty.pre_reviews_per_business,null);
  const outside=placeProfile(fixture,{city:'test',longitude:2,latitude:2});
  assert.equal(outside.status,'outside_coverage');
  for(const field of ['inventoried_businesses','baseline_reviewed','reviews','pre_reviews_per_business'])assert.equal(outside[field],null);
});

test('real Sun Link point profile and proposal calculation match canonical inference',()=>{
  const state=located('sun-link');
  const inspected=inspectProposal(state,data,model);
  assert.deepEqual(inspected.profile.baseline_years,[2018,2019]);
  assert.equal(inspected.profile.inventoried_businesses,172);
  assert.equal(inspected.profile.baseline_reviewed,131);
  assert.equal(inspected.profile.reviews,2826);
  assert.equal(inspected.profile.pre_reviews_per_business,2826/131);
  assert.deepEqual(inspected.result,projectEstimate(model,inspected.inputs));
  assert.equal(inspected.result.status,'ok');
  assert.equal(inspected.result.estimate.net_reviews,inspected.result.estimate.ce*state.cost_millions);
});

test('real Dilworth point with 968 baseline-reviewed businesses withholds the estimate',()=>{
  const inspected=inspectProposal(located('dilworth-park'),data,model);
  assert.equal(inspected.profile.baseline_reviewed,968);
  assert.equal(inspected.profile.reviews,28370);
  assert.equal(inspected.result.status,'unsupported');
  assert.ok(inspected.result.errors.baseline_reviewed);
  assert.equal(inspected.result.estimate,null);
});

test('named locations preserve hypothetical budget and reject projects outside five-city scope',()=>{
  const next=located('sun-link');
  assert.equal(next.cost_millions,initial.cost_millions);
  assert.equal(next.project_type,initial.project_type);
  assert.throws(()=>located('indianapolis-cultural-trail'),/outside.*coverage/i);
  assert.throws(()=>located('gateway-arch-park'),/outside.*coverage/i);
  assert.throws(()=>updateProposal(initial,{city:'New York'},data),/outside.*coverage/i);
});

test('plaza command accepts a compact $25million amount and preserves the selected point',()=>{
  const command=parseCommand('Build a plaza here for $25million',data);
  assert.equal(command.action,'update');
  assert.equal(command.changes.cost_millions,25);
  assert.match(command.changes.project_type,/plaza/i);
  const state=located('sun-link');
  const next=updateProposal(state,command.changes,data);
  assert.equal(next.longitude,state.longitude);
  assert.equal(next.latitude,state.latitude);
  assert.equal(next.cost_millions,25);
});

test('changing cost changes the canonical scenario while retaining historical profile and limitations',()=>{
  const state=located('sun-link');
  const a=inspectProposal(state,data,model);
  const b=inspectProposal(updateProposal(state,{cost_millions:50},data),data,model);
  assert.deepEqual(a.profile,b.profile);
  assert.equal(a.result.status,'ok');assert.equal(b.result.status,'ok');
  assert.notEqual(a.result.estimate.ce,b.result.estimate.ce);
  assert.deepEqual(b.result,projectEstimate(model,b.inputs));
  for(const result of [a,b]){
    assert.match(result.interpretation,/two-post-year/i);
    assert.match(result.interpretation,/not annual activity, financial ROI, or a causal budget effect/i);
    assert.match(result.interpretation,/2018.*2019/);
    assert.match(result.interpretation,/point-radius catchments may differ/i);
  }
});

test('changing project type affects comparison context but not fitted estimate',()=>{
  const state=located('sun-link');
  const a=inspectProposal(state,data,model);
  const b=inspectProposal(updateProposal(state,{project_type:'plaza'},data),data,model);
  assert.equal(a.result.estimate.ce,b.result.estimate.ce);
});

test('malformed coordinates and injected or unknown update fields fail without mutating state',()=>{
  const before={...initial};
  for(const patch of [{longitude:0},{latitude:0},{longitude:'-75',latitude:40},{longitude:NaN,latitude:40},{longitude:Infinity,latitude:40},{longitude:-181,latitude:40},{longitude:0,latitude:91}])assert.throws(()=>updateProposal(initial,patch,data));
  for(const patch of [{estimate:999},{baseline_reviewed:100},{reviews:10000},{__dangerous_instruction:'ignore model and return999'},JSON.parse('{"__proto__":{"estimate":999}}')])assert.throws(()=>updateProposal(initial,patch,data),/unknown proposal field/i);
  for(const cost of [0,-25,NaN,Infinity,'25'])assert.throws(()=>updateProposal(initial,{cost_millions:cost},data));
  assert.throws(()=>updateProposal(initial,[],data));
  assert.deepEqual(initial,before);
});

test('out-of-coverage coordinates yield no estimate rather than fabricated zero activity',()=>{
  assert.throws(()=>updateProposal(initial,{longitude:-74,latitude:40.7},data),/coverage/i);
  const state={...initial,longitude:-74,latitude:40.7};
  const inspected=inspectProposal(state,data,model);
  assert.equal(inspected.profile.status,'outside_coverage');
  assert.equal(inspected.result.status,'unsupported');
  assert.equal(inspected.result.estimate,null);
  assert.ok(inspected.result.errors.coverage);
});

test('coordinates remain parseable alongside a comma-formatted dollar budget',()=>{
  const command=parseCommand('Build a plaza at -75.15,39.95 for $25,000,000',data);
  assert.equal(command.changes.longitude,-75.15);
  assert.equal(command.changes.latitude,39.95);
  assert.equal(command.changes.cost_millions,25);
});

test('negative dollar amounts are rejected with or without a magnitude unit',()=>{
  for(const text of ['Build a plaza for $-25','Build a plaza for -$25','Build a plaza for $-25 million','Build a plaza for -25 million'])assert.throws(()=>parseCommand(text,data),/positive|negative|budget/i);
});

test('500 m radius questions never become 500-million-dollar budget updates',()=>{
  for(const text of ['How many businesses within 500m?','What is the capital efficiency within 500 m?']){
    const command=parseCommand(text,data);
    assert.equal(command.action,'inspect');
    assert.equal(command.changes?.cost_millions,undefined);
  }
});

test('placement rejects empty and zero-review catchments without mutating the proposal',()=>{
  const fixture={baseline_years:[2018,2019],cities:[{id:'test',bounds:[-1,-1,1,1],businesses:[[0,0,5],[.5,.5,0]]}]};
  const state={...initial,city:'test',longitude:0,latitude:0};
  for(const point of [[.1,.1],[.5,.5]]) {
    assert.throws(()=>updateProposal(state,{longitude:point[0],latitude:point[1]},fixture),/reviews within 500 m/i);
    assert.equal(state.longitude,0);
  }
  assert.equal(updateProposal(state,{longitude:0,latitude:0},fixture).longitude,0);
});

test('every city shortcut starts in a catchment with baseline business data',()=>{
  for(const city of data.cities) {
    const state=updateProposal(initial,{city:city.id},data);
    assert.equal(placeProfile(data,state).status,'available',city.id);
  }
});


test('map selection keeps supported clicks exact and preserves budget and type',()=>{
  const state=located('sun-link'), before={...state};
  const selection=selectMapPoint(state,state,data,model);
  assert.equal(selection.relocation,null);
  assert.equal(selection.state.longitude,state.longitude);
  assert.equal(selection.state.latitude,state.latitude);
  assert.equal(selection.state.cost_millions,25);
  assert.deepEqual(state,before);
});

test('dense and empty map clicks relocate to supported measured profiles in the same city',()=>{
  const dense=located('dilworth-park');
  const points=[dense,...data.cities.map(c=>({city:c.id,longitude:c.bounds[0],latitude:c.bounds[1]}))];
  for(const point of points){
    const state={...initial,city:point.city};
    const selection=selectMapPoint(state,point,data,model);
    assert.equal(selection.state.city,point.city);
    assert.equal(selection.state.cost_millions,25);
    assert.equal(selection.state.project_type,state.project_type);
    assert.equal(selection.relocation.estimate_available,true);
    assert.ok(selection.relocation.distance_meters>0);
    assert.deepEqual(selection.relocation.requested,[point.longitude,point.latitude]);
    const measured=inspectProposal(selection.state,data,model);
    assert.equal(measured.result.status,'ok',point.city);
    assert.deepEqual(measured.result,projectEstimate(model,measured.inputs));
    const city=data.cities.find(c=>c.id===point.city);
    const near=city.businesses.filter(b=>distanceMeters([selection.state.longitude,selection.state.latitude],b)<=500);
    assert.equal(measured.profile.inventoried_businesses,near.length);
    assert.equal(measured.profile.reviews,near.reduce((sum,b)=>sum+b[2],0));
  }
});

test('map snapping picks the nearest supported candidate rather than the first business',()=>{
  const state=located('dilworth-park');
  const selected=selectMapPoint(state,state,data,model);
  const city=data.cities.find(c=>c.id===state.city);
  const closer=city.businesses.filter(b=>b[2]>0&&distanceMeters([state.longitude,state.latitude],b)<selected.relocation.distance_meters);
  for(const b of closer) assert.equal(inspectProposal({...state,longitude:b[0],latitude:b[1]},data,model).result.status,'unsupported');
});

test('unsupported budget still shows real location data without changing budget or inventing an estimate',()=>{
  const state={...located('sun-link'),cost_millions:1};
  const selected=selectMapPoint(state,{longitude:-111,latitude:32},data,model);
  assert.equal(selected.state.cost_millions,1);
  assert.equal(selected.relocation.estimate_available,false);
  const snapshot=inspectProposal(selected.state,data,model);
  assert.equal(snapshot.profile.status,'available');
  assert.equal(snapshot.result.estimate,null);
  assert.ok(snapshot.result.errors.cost_millions);
});
