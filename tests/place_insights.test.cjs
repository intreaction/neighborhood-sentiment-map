const test=require('node:test');
const assert=require('node:assert/strict');
const {scenarioInsights,historicalSeries,linearFit}=require('../src/place_insights.cjs');
const core=require('../src/place_core.cjs');
const data=require('../web/place-data.json'),model=require('../web/place-model.json'),history=require('../web/place-history.json');
const p=data.projects.find(p=>p.id==='the-rail-park');
const state={city:p.city_id,longitude:p.center[0],latitude:p.center[1],project_id:p.id,cost_millions:25,project_type:'Civic plaza / transit access'};
test('engagement charts retain the model total and exact regression decomposition',()=>{
 const snapshot=core.inspectProposal(state,data,model),info=scenarioInsights(snapshot,model);
 assert.equal(info.timeline.at(-1).y,snapshot.result.estimate.net_reviews);
 assert.equal(info.timeline[2].y,info.total/2);
 assert.equal(info.error.low,snapshot.result.empirical_error.low*25);
 assert.equal(info.baselineShare,info.total/snapshot.profile.reviews*100);
 assert.ok(Math.abs(info.intercept+info.contributions.reduce((sum,c)=>sum+c.value,0)-snapshot.result.estimate.ce)<1e-10);
 const current=info.sensitivity.find(v=>v.x===25);assert.equal(current.y,info.total);
});
test('unsupported predictions never become a timeline or fabricated zero',()=>{
 const snapshot=core.inspectProposal({...state,cost_millions:1},data,model);
 assert.equal(scenarioInsights(snapshot,model),null);
 const info=scenarioInsights(core.inspectProposal(state,data,model),model);
 assert.ok(info.sensitivity.some(p=>p.y===null),'unsupported budget combinations are gaps');
});
test('negative model totals and error bounds remain negative without clipping',()=>{
 const snapshot=core.inspectProposal(state,data,model);
 snapshot.result.estimate.net_reviews=-100;
 const info=scenarioInsights(snapshot,model);assert.equal(info.timeline.at(-1).y,-100);assert.equal(info.timeline[2].y,-50);assert.ok(info.error.low<0);
});
test('historical trends use actual annual counts and only pre-opening data for OLS',()=>{
 for(const p of history.projects){
  const s=historicalSeries(p);if(!s)continue;
  const pre=s.near.points.filter(p=>p.period==='pre');
  assert.ok(Math.abs(pre.reduce((sum,p)=>sum+p.y,0)/pre.length-100)<1e-10);
  for(const group of ['near','far']) {
   const fit=linearFit(s[group].points.filter(p=>p.period!=='post'));
   assert.deepEqual(s[group].fit,fit);
   for(const point of s[group].points)assert.equal(point.count,p.periods[group][point.period].by_year[point.x]);
  }
 }
});
test('ordinary least squares fits known trend and withholds insufficient observations',()=>{
 assert.deepEqual(linearFit([{x:0,y:2},{x:1,y:5},{x:2,y:8}]),{slope:3,intercept:2,n:3});
 assert.equal(linearFit([{x:0,y:2},{x:1,y:5}]),null);
});

test('topic changes compare near and farther changes without implying predictions',()=>{
 const {historicalTopics}=require('../src/place_insights.cjs');
 const period=(share,negative,count)=>({n_reviews:100,topics:{walking_accessibility:{share,negative_share:negative,n_reviews:count,negative_reviews:count/2}}});
 const p={periods:{near:{pre:period(.1,.04,10),post:period(.2,.02,20)},far:{pre:period(.05,.01,5),post:period(.08,.015,8)}}};
 const topic=historicalTopics(p)[0];assert.ok(Math.abs(topic.value-7)<1e-10);assert.equal(topic.sparse,true);
 const complaints=historicalTopics(p,'complaints')[0];assert.ok(Math.abs(complaints.value+2.5)<1e-10);
 assert.equal(historicalTopics({periods:{near:{pre:{n_reviews:0}},far:{}}}).length,0);
});
test('exported historical topics preserve the source review shares and counts',()=>{
 const {historicalTopics}=require('../src/place_insights.cjs');
 const evidence=require('../data/derived/project_evidence.json');
 for(const p of history.projects){
  const source=evidence.projects.find(s=>s.id===p.id);
  for(const row of historicalTopics(p)) {
   assert.equal(row.preCount,source.periods.near.pre.topics[row.topic].n_reviews);
   assert.equal(row.postCount,source.periods.near.post.topics[row.topic].n_reviews);
  }
 }
});
