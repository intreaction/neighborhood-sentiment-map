import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {createPlaceTools,registerPlaceTools} from '../src/place_tools.mjs';
import {zipProfile} from '../src/place_measures.mjs';
import {areaAnchor} from '../src/place_area_math.mjs';

const load=f=>JSON.parse(readFileSync(new URL(`../web/${f}`,import.meta.url)));
const data=load('place-data.json'),areas=load('place-areas.json'),history=load('place-history.json'),model=load('place-model.json'),map=load('place-map.json');
const validation=JSON.parse(readFileSync(new URL('../data/derived/text_validation/metrics.json',import.meta.url)));

// A fake page that records what the tools asked it to show.
function fakeView(){
  const log=[],state={section:'map',city:'Philadelphia',zip:'19123',focus:'activity',measure:null,past_projects:{kind:'all',project_id:null,chart:'engagement'}};
  return {log,state,view:{
    current:()=>JSON.parse(JSON.stringify(state)),
    showOnMap:a=>{log.push(['map',a]);if(a.city)state.city=a.city;if(a.zip)state.zip=a.zip;if(a.focus)state.focus=a.focus;},
    showPastProjects:a=>{log.push(['past',a]);Object.assign(state.past_projects,Object.fromEntries(Object.entries(a).filter(([,v])=>v!=null)));state.section=a.chart?'project_charts':'past_projects';},
    goTo:s=>{log.push(['goto',s]);state.section=s;},
    highlightMeasure:k=>{log.push(['measure',k]);state.measure=k;state.section='zip_profile';},
    zoom:d=>log.push(['zoom',d]),
    anchors:id=>Object.fromEntries(map.cities.find(c=>c.id===id).features.map(f=>[f.properties.zip,areaAnchor(f)]))
  }};
}
const toolsFor=view=>createPlaceTools({data,areas,history,model,validation,view});
const call=async(tools,name,args={})=>tools.find(t=>t.name===name).execute(args);

test('every tool has a schema, annotations and a spoken result',async()=>{
  const {view}=fakeView(),tools=toolsFor(view);
  assert.deepEqual(tools.map(t=>t.name),['get_place_lab_guide','describe_screen','navigate','go_to','move_to_neighbor','get_zip_profile','find_zips','compare_past_projects','get_project_history','define_term','show_on_map','show_past_projects']);
  for(const t of tools){
    assert.equal(t.inputSchema.additionalProperties,false,t.name);
    assert.equal(typeof t.annotations.readOnlyHint,'boolean',t.name);
    assert.ok(t.description.length>60,t.name);
  }
  const guide=await call(tools,'get_place_lab_guide');
  assert.equal(guide.ok,true);assert.equal(guide.past_projects.length,11);assert.match(guide.say,/past projects/);
});

test('ZIP profile matches the numbers the page shows',async()=>{
  const tools=toolsFor(fakeView().view);
  const r=await call(tools,'get_zip_profile',{zip:'19134'});
  const page=zipProfile(areas.cities.find(c=>c.id==='Philadelphia').areas,'19134');
  assert.equal(r.city,'Philadelphia');
  for(const row of r.measures){const p=page.find(x=>x.measure.key===row.measure);assert.equal(row.rank,p.rank);assert.equal(row.limited_data,p.value===null);}
  assert.equal(r.measures.find(m=>m.measure==='access_discussion').display,'3.3%');
  assert.match(r.say,/19134/);
});

test('find_zips ranks, filters and reports limited data',async()=>{
  const tools=toolsFor(fakeView().view);
  const r=await call(tools,'find_zips',{city:'philly',measure:'access_discussion',filters:[{measure:'poverty',min:20}],limit:3});
  assert.equal(r.ok,true);assert.equal(r.city,'Philadelphia');assert.equal(r.zips.length,3);
  assert.ok(r.zips.every(z=>z.poverty>=20));assert.ok(r.zips[0].value>=r.zips[1].value);
  assert.ok(r.excluded_for_limited_data>0);
});

test('past-project comparison is descriptive and carries reliability',async()=>{
  const tools=toolsFor(fakeView().view);
  const r=await call(tools,'compare_past_projects',{kind:'trail'});
  assert.equal(r.projects.length,4);assert.equal(r.does_kind_predict.answer,'No');
  assert.match(r.reliability.negative_access_change_pp,/Low reliability/);
  const sun=await call(tools,'get_project_history',{project_id:'sun-link'});
  assert.ok(sun.adjusted_changes.engagement_change_pct<0);
  assert.equal((await call(tools,'get_project_history',{project_id:'water-works-park'})).adjusted_changes,null);
});

test('errors explain how to recover',async()=>{
  const tools=toolsFor(fakeView().view);
  const bad=await call(tools,'get_zip_profile',{zip:'99999'});
  assert.equal(bad.ok,false);assert.ok(bad.hint);
  const city=await call(tools,'find_zips',{city:'Boston',measure:'income'});
  assert.ok(city.valid_values.includes('Philadelphia'));
  assert.match((await call(tools,'get_place_lab_guide',{budget:5})).error,/Unexpected argument/);
  assert.match((await call(tools,'navigate',{})).error,/Missing required/);
  assert.match((await call(tools,'show_past_projects',{kind:'civic',project_id:'lafitte'})).error,/Trail/);
});

test('navigate moves between sections and steps within them',async()=>{
  const f=fakeView(),tools=toolsFor(f.view);
  let r=await call(tools,'navigate',{direction:'down'});
  assert.equal(r.section,'zip_profile');
  r=await call(tools,'navigate',{direction:'right'});
  assert.deepEqual(f.log.at(-1),['measure','listings']);
  r=await call(tools,'navigate',{direction:'left'});
  assert.deepEqual(f.log.at(-1),['measure','area'],'left wraps to the last measure');
  await call(tools,'navigate',{direction:'down'});
  r=await call(tools,'navigate',{direction:'right'});
  assert.deepEqual(f.log.at(-1),['past',{kind:'trail'}]);
  await call(tools,'go_to',{section:'project_charts'});
  await call(tools,'navigate',{direction:'right'});
  assert.deepEqual(f.log.at(-1),['past',{chart:'sentiment'}]);
  r=await call(tools,'navigate',{direction:'down',steps:5});
  assert.equal(r.section,'notes');
  r=await call(tools,'navigate',{direction:'down'});
  assert.match(r.say,/bottom/);
});

test('map moves go to the geographic neighbour',async()=>{
  const f=fakeView(),tools=toolsFor(f.view),anchors=f.view.anchors('Philadelphia');
  const r=await call(tools,'move_to_neighbor',{direction:'north'});
  assert.equal(r.ok,true);assert.equal(r.moved_from,'19123');
  assert.ok(anchors[f.state.zip][1]>anchors['19123'][1],'moved north');
  const before=f.state.zip;
  await call(tools,'navigate',{direction:'left'});
  assert.ok(anchors[f.state.zip][0]<anchors[before][0],'left moves west');
  await call(tools,'navigate',{direction:'in'});
  assert.deepEqual(f.log.at(-1),['zoom','in']);
});

test('show tools keep a project inside the current filter or switch to its kind',async()=>{
  const f=fakeView(),tools=toolsFor(f.view);
  await call(tools,'show_past_projects',{project_id:'the-rail-park'});
  assert.deepEqual(f.log.at(-1),['past',{kind:undefined,project_id:'the-rail-park',chart:undefined}]);
  f.state.past_projects.kind='civic';
  await call(tools,'show_past_projects',{project_id:'the-rail-park'});
  assert.equal(f.log.at(-1)[1].kind,'trail');
  const r=await call(tools,'show_on_map',{zip:'37203',focus:'poverty'});
  assert.equal(r.ok,true);assert.deepEqual(f.log.find(e=>e[0]==='map'&&e[1].zip==='37203')[1],{city:'Nashville',zip:'37203',focus:'poverty'});
});

test('define_term finds glossary entries by name',async()=>{
  const tools=toolsFor(fakeView().view);
  const r=await call(tools,'define_term',{term:'comparison area'});
  assert.equal(r.key,'comparison_area');assert.match(r.link,/methods\.html#term-comparison_area/);
});

test('WebMCP registration returns plain results for the browser to serialise',async()=>{
  const tools=toolsFor(fakeView().view),registered=[];
  assert.equal(await registerPlaceTools(undefined,tools),false);
  assert.equal(await registerPlaceTools({registerTool:t=>registered.push(t)},tools),true);
  const out=await registered.find(t=>t.name==='define_term').execute({term:'VADER'},{signal:null});
  assert.equal(out.ok,true);assert.match(out.say,/VADER/);
  assert.equal((await registered.find(t=>t.name==='get_place_lab_guide').execute(undefined)).ok,true);
  let provided=null;
  assert.equal(await registerPlaceTools({provideContext:c=>{provided=c;}},tools),true);
  assert.equal(provided.tools.length,tools.length);
});
