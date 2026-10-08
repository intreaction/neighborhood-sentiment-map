import test from 'node:test';
import assert from 'node:assert/strict';
import {request as httpRequest} from 'node:http';
import {createPlaceService} from '../src/place_service.mjs';
import {createBridgeServer} from '../src/serve_place.mjs';
import {DEFAULT_TIME} from '../src/place_timeline.mjs';
const service=createPlaceService(import.meta.url);
const snapshot={section:'map',city:'Tucson',zip:'85701',focus:'activity',measure:null,past_projects:{kind:'all',project_id:'lafitte',chart:'engagement'},time:{setting:DEFAULT_TIME}};

test('server rankings distinguish review density from total reviews and plan a single combined display',async()=>{
  const density=await service.plan('rank_areas',{city:'Tucson',measure:'engagement',limit:1,show:true});
  const reviews=await service.plan('rank_areas',{city:'Tucson',measure:'reviews',limit:1});
  assert.equal(density.result.zips[0].zip,'85701');assert.equal(reviews.result.zips[0].zip,'85719');
  assert.equal(density.result.excluded_for_limited_data,6);
  assert.deepEqual(density.actions,[{tool:'show_on_map',arguments:{city:'Tucson',zip:'85701',focus:'activity'}}]);
  assert.equal(density.result.period.level,'2019–2021');
});

test('period-specific queries isolate values and labels across contexts',async()=>{
  const defaultResult=await service.plan('get_area_profile',{zip:'19134'});
  const quarter=await service.plan('get_area_profile',{zip:'19134',time:{period:'2016Q3'}});
  const nextDefault=await service.plan('get_area_profile',{zip:'19134'});
  const row=r=>r.result.measures.find(m=>m.measure==='engagement');
  assert.notEqual(row(defaultResult).value,row(quarter).value);
  assert.match(row(quarter).period,/Q3 2016/);assert.match(row(quarter).caution,/50 reviews/);assert.match(row(nextDefault).period,/2019–2021/);
  assert.deepEqual(defaultResult.result,nextDefault.result);
  const monthly=await service.plan('rank_areas',{city:'Tucson',measure:'engagement',time:{grain:'month',period:'2016-07',smooth:3},show:true});
  assert.equal(monthly.context.time.setting.grain,'month');assert.equal(monthly.actions[0].tool,'set_map_time');
});

test('context inference, comparisons, timelines and historical exclusions are supported',async()=>{
  const inferred=await service.plan('rank_areas',{measure:'engagement',limit:1},snapshot);assert.equal(inferred.result.city,'Tucson');
  await assert.rejects(service.plan('rank_areas',{measure:'engagement'}),/Specify city/);
  const compare=await service.plan('compare_areas',{zips:['85701','19107']});assert.equal(compare.result.areas[0].city,'Tucson');assert.equal(compare.result.areas[1].city,'Philadelphia');
  const timeline=await service.plan('get_area_timeline',{zip:'85701',grain:'month',smooth:3});assert.equal(timeline.result.series.length,120);
  const excluded=await service.plan('get_project',{project_id:'water-works-park'});assert.equal(excluded.result.adjusted_changes,null);
  const negative=await service.plan('compare_projects',{});assert.match(negative.result.reliability.negative_access_change_pp,/Low reliability/);
});

test('schemas reject malformed and unexpected inputs before page dispatch',async()=>{
  for(const args of [{measure:'unknown',city:'Tucson'},{measure:'engagement',city:'Tucson',limit:NaN},{measure:'engagement',city:'Tucson',filters:[{measure:'poverty',min:'20'}]}])await assert.rejects(service.plan('rank_areas',args));
  await assert.rejects(service.plan('set_view',{zip:85701}),/must be string/);
  await assert.rejects(service.plan('set_view',{javascript:'alert(1)'}),/Unknown/);
  await assert.rejects(service.plan('set_view',{city:'Boston'}),/Unknown city/);
  await assert.rejects(service.plan('get_area_profile',{zip:'85701',time:{period:'2030Q1'}}),/not a period/);
});

test('HTTP bridge authenticates, acknowledges commands, deduplicates retries and tracks manual context',async t=>{
  const bridge=createBridgeServer({commandTimeoutMs:200});
  await new Promise(resolve=>bridge.server.listen(0,'127.0.0.1',resolve));
  const url=`http://127.0.0.1:${bridge.server.address().port}`;
  const controllers=[];
  t.after(async()=>{controllers.forEach(c=>c.abort());for(const s of bridge.sessions.values())s.stream?.end();bridge.server.closeAllConnections();await new Promise(resolve=>bridge.server.close(resolve));});
  const request=async(path,value,extra={})=>{
    const r=await fetch(url+path,{method:value===undefined?'GET':'POST',headers:{Authorization:`Bearer ${bridge.token}`,...(value===undefined?{}:{'Content-Type':'application/json'}),...extra},body:value===undefined?undefined:JSON.stringify(value)});
    return {status:r.status,value:await r.json()};
  };
  assert.equal((await fetch(url+'/api/tools')).status,401);
  assert.equal((await request('/api/tools',undefined,{Origin:'https://example.com'})).status,403);
  assert.equal(await new Promise(resolve=>{const req=httpRequest(url+'/api/tools',{headers:{Host:'attacker.example'}},res=>{res.resume();resolve(res.statusCode);});req.end();}),403);
  assert.equal((await request('/api/tools')).value.tools.length,11);
  assert.equal((await request('/api/call',{tool:'rank_areas',arguments:{city:'Tucson',measure:'engagement',limit:1}})).value.zips[0].zip,'85701');
  assert.equal((await request('/api/call',{tool:'navigate',arguments:{direction:'down'}})).status,409);
  const register=async()=>{
    const r=await request('/api/connect',{}, {Origin:url});const id=r.value.session_id;
    await request(`/api/sessions/${id}/state`,{view:snapshot,revision:1});
    const abort=new AbortController();controllers.push(abort);
    const events=await fetch(url+`/api/sessions/${id}/events`,{headers:{Authorization:`Bearer ${bridge.token}`},signal:abort.signal});
    return {id,reader:events.body.getReader()};
  };
  const page=await register();let eventCount=0;
  const nextCommand=async()=>{
    let accumulated='';
    while(true){const {value,done}=await page.reader.read();if(done)throw new Error('SSE closed');accumulated+=new TextDecoder().decode(value);const hit=accumulated.match(/event: command\ndata: ([^\n]+)\n/);if(hit){eventCount++;return JSON.parse(hit[1]);}}
  };
  const payload={tool:'rank_areas',arguments:{measure:'engagement',limit:1,show:true},command_id:'dedup'};
  const pending=request('/api/call',payload),command=await nextCommand();
  assert.equal(command.expected_revision,1);assert.equal(command.actions[0].arguments.zip,'85701');
  await request(`/api/sessions/${page.id}/results`,{id:command.id,ok:true,result:{ok:true,say:'Applied'},view:snapshot,revision:2});
  const acknowledged=await pending;assert.equal(acknowledged.value.display.status,'applied');
  assert.deepEqual((await request('/api/call',payload)).value,acknowledged.value);assert.equal(eventCount,1);
  assert.equal((await request('/api/call',{...payload,arguments:{measure:'reviews'}})).status,409);
  await request(`/api/sessions/${page.id}/state`,{view:{...snapshot,city:'Philadelphia',zip:'19107'},revision:3});
  assert.equal((await request('/api/call',{tool:'rank_areas',arguments:{measure:'engagement',limit:1}})).value.city,'Philadelphia');
  assert.equal((await request(`/api/sessions/${page.id}/state`,{view:snapshot,revision:1})).status,409);
  const timeout=request('/api/call',{tool:'navigate',arguments:{direction:'down'}});await nextCommand();assert.equal((await timeout).status,504);
  const duplicate=await request('/api/connect',{session_id:page.id},{Origin:url});assert.notEqual(duplicate.value.session_id,page.id,'a duplicated tab receives its own session');
  await register();assert.equal((await request('/api/call',{tool:'get_context'})).status,409);
  assert.equal((await request('/api/call',{tool:'get_context',session_id:page.id})).status,200);
});
