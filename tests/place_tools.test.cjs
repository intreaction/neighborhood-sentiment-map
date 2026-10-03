const test=require('node:test');
const assert=require('node:assert/strict');
const {createPlaceTools,registerPlaceTools}=require('../src/place_tools.cjs');
const core=require('../src/place_core.cjs');
const data=require('../web/place-data.json');
const model=require('../web/place-model.json');

test('optional agent tools use the same real profile and prediction as human controls',async()=>{
  const project=data.projects.find(p=>p.id==='the-rail-park');
  let state={city:project.city_id,longitude:project.center[0],latitude:project.center[1],project_id:project.id,cost_millions:25,project_type:'Civic plaza / transit access'};
  const tools=createPlaceTools({getCatalog:()=>({source:data.source_label}),onTool:async(name,args)=>{
    if(name==='update_proposal')state=core.updateProposal(state,args,data);
    return {ok:true,...core.inspectProposal(state,data,model)};
  }});
  assert.deepEqual(tools.map(t=>t.name),['inspect_place_catalog','inspect_proposal','update_proposal']);
  const result=await tools[2].execute({cost_millions:50});
  assert.equal(result.proposal.cost_millions,50);
  assert.equal(result.profile.baseline_reviewed,124);
  assert.equal(result.result.estimate.ce,core.inspectProposal(state,data,model).result.estimate.ce);
  result.proposal.cost_millions=999;
  assert.equal(state.cost_millions,50,'tool returns must not expose mutable live state');
  const before={...state};
  assert.equal((await tools[2].execute({cost_millions:10,longitude:0})).ok,false);
  assert.deepEqual(state,before,'invalid updates stay atomic');
});
test('catalog and inspection reject unexpected arguments',async()=>{
  let calls=0;
  const tools=createPlaceTools({getCatalog:()=>({source:'historical'}),onTool:()=>{calls++;return {};}});
  assert.equal((await tools[0].execute({cost_millions:30})).ok,false);
  assert.equal((await tools[1].execute({latitude:1})).ok,false);
  assert.equal(calls,0);
  assert.deepEqual(await tools[0].execute({}),{ok:true,source:'historical'});
});
test('registration is optional and tools carry read-only annotations',async()=>{
  const tools=createPlaceTools({getCatalog:()=>({}),onTool:()=>({})});
  assert.equal(await registerPlaceTools(undefined,tools),false);
  const registered=[];
  assert.equal(await registerPlaceTools({registerTool:t=>registered.push(t)},tools),true);
  assert.deepEqual(registered.map(t=>t.annotations.readOnlyHint),[true,true,false]);
  assert.equal(registered[2].inputSchema.additionalProperties,false);
});
