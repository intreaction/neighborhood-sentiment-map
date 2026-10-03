import {createPlaceMap} from './place_map.js';
import core from './place_core.cjs';
import agentTools from './place_tools.cjs';
import {renderInsights,renderHistory,renderTopics,decisionExport} from './place_charts.js';

const $=id=>document.getElementById(id);
const number=(n, digits=0)=>Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits}):'—';
let data, model, mapData, history, state, initial, scene, latest, lastCity, editingBudget=false;
function locationTitle() {
  const project=data.projects.find(p=>p.id===state.project_id);
  return project?'Near '+project.name:`${number(state.latitude,4)}, ${number(state.longitude,4)}`;
}
function catalog(){return {source:data.source_label,baseline_years:data.baseline_years,available_cities:data.cities.map(({id,label,bounds})=>({id,label,bounds})),available_project_locations:data.projects.filter(p=>p.city_id).map(({id,name,city_id,center})=>({id,name,city_id,center})),project_types:[...new Set([...core.TYPES,...data.projects.map(p=>p.project_type)])]};}
function render() {
  latest=core.inspectProposal(state,data,model);
  const {profile,result}=latest;
  const city=data.cities.find(c=>c.id===state.city);
  $('mapTitle').textContent=city.label;
  $('citySelect').value=state.city;
  $('landmarkSelect').value=state.project_id||'';
  $('longitude').value=state.longitude.toFixed(6);$('latitude').value=state.latitude.toFixed(6);
  $('projectType').value=state.project_type;if(!editingBudget)$('budget').value=state.cost_millions;
  $('selectionLabel').textContent=locationTitle();
  $('formStatus').textContent=`${locationTitle()} · $${number(state.cost_millions,1)}M proposal. ${result.status==='ok'?'Analysis updated below.':'Estimate withheld; see the support explanation below.'}`;
  $('budget').setCustomValidity('');$('budget').removeAttribute('aria-invalid');
  $('businessCount').textContent=number(profile.baseline_reviewed);
  $('reviewRate').textContent=number(profile.pre_reviews_per_business,1);
  $('inventoryNote').textContent=profile.status==='outside_coverage'?'Outside the mapped data coverage.':`${number(profile.inventoried_businesses)} Yelp-listed businesses in the archive. Counts are historical, not a current census.`;
  $('reviewNote').textContent=profile.status==='outside_coverage'?'Choose a point in one of the five covered regions.':`${number(profile.reviews)} reviews across two baseline years. All zero-review businesses remain in the inventory count.`;
  $('estimate').textContent=result.status==='ok'?number(result.estimate.ce,1):'Withheld';
  $('estimateNote').textContent=result.status==='ok'?'A fitted activity association. A larger budget does not establish a larger causal impact.':Object.values(result.errors).join(' ');
  $('uncertainty').textContent=result.empirical_error?`${number(result.empirical_error.low,1)} to ${number(result.empirical_error.high,1)} excess reviews / $1M. Historical city-holdout error envelope, not a confidence interval. City-holdout mean absolute error: ${number(result.empirical_error.mae,1)}.`:'An estimate is shown only when the measured inputs and their combination fall inside historical model support.';
  renderInsights(latest,model,history);
  $('comparables').replaceChildren();
  if(!result.nearest_cases.length) {
    const p=document.createElement('p');p.textContent='Choose a location and budget within model support to see comparable profiles. All historical projects remain in the evidence library.';$('comparables').append(p);
  }
  for(const row of result.nearest_cases) {
    const link=document.createElement('a');link.className='comparable';link.href='projects.html?project='+encodeURIComponent(row.id);
    const div=document.createElement('div'),title=document.createElement('h3'),note=document.createElement('p'),arrow=document.createElement('span');
    title.textContent=row.project;note.textContent=`${row.city} · ${row.same_type?'Same project type · ':''}Observed ${number(row.observed_ce,1)} reviews / $1M`;arrow.textContent='↗';arrow.setAttribute('aria-hidden','true');div.append(title,note);link.append(div,arrow);$('comparables').append(link);
  }
  if(scene) {
    if(lastCity!==state.city) { const geometry=mapData.cities.find(c=>c.id===state.city);scene.setCity({...city,...geometry,projects:data.projects.filter(p=>p.city_id===city.id)});lastCity=state.city; }
    scene.setSelection({longitude:state.longitude,latitude:state.latitude,radiusMeters:500});
    scene.setMetrics?.({title:locationTitle(),ce:result.estimate?.ce ?? null,costMillions:state.cost_millions,businesses:profile.baseline_reviewed,subtitle:'2018–2019 baseline · two-post-year proxy'});
  }
}
function change(changes) {
  const next=core.updateProposal(state,changes,data);state=next;render();return latest;
}
function reset(){state={...initial};render();scene?.reset();}
async function onTool(name,args) {
  try {
    if(name==='update_proposal') {const snapshot=change(args);return {ok:true,...snapshot,place:locationTitle()};}
    if(name==='inspect_proposal') {if(!args || typeof args!=='object' || Array.isArray(args)||Object.keys(args).length)throw new Error('Inspection accepts an empty object.');return {ok:true,...latest,place:locationTitle()};}
    return {ok:false,error:'Unknown tool. Use update_proposal or inspect_proposal.'};
  }catch(error){return {ok:false,error:error.message,current:latest};}
}
function sceneStatus(status) {
  $('sceneStatus').textContent=typeof status==='string'?status:status.message||'';

}
async function init() {
  const assets=await Promise.all(['place-data.json','place-map.json','place-model.json','place-history.json'].map(async path=>{const r=await fetch(path);if(!r.ok)throw new Error('Missing local asset: '+path);return r.json();}));
  [data,mapData,model,history]=assets;
  const pilot=data.projects.find(p=>p.id==='the-rail-park');
  initial={city:pilot.city_id,longitude:pilot.center[0],latitude:pilot.center[1],project_id:pilot.id,project_type:'Civic plaza / transit access',cost_millions:25};state={...initial};
  for(const city of data.cities){const option=new Option(city.label,city.id);$('citySelect').add(option);}
  $('citySelect').disabled=false;
  for(const project of history.projects)$('historyProject').add(new Option(project.project,project.id));
  $('historyProject').value=pilot.id;
  $('historyProject').addEventListener('change',()=>renderHistory(history,$('historyProject').value));
  $('topicMeasure').addEventListener('change',()=>renderTopics(history,$('historyProject').value));
  for(const project of data.projects.filter(p=>p.city_id))$('landmarkSelect').add(new Option(`${project.name} · ${project.city_label}`,project.id));
  for(const type of [...new Set([...core.TYPES,...data.projects.map(p=>p.project_type)])])$('projectType').add(new Option(type,type));
  $('citySelect').addEventListener('change',()=>{change({city:$('citySelect').value});});
  $('landmarkSelect').addEventListener('change',()=>{if($('landmarkSelect').value)change({project_id:$('landmarkSelect').value});});
  $('projectType').addEventListener('change',()=>change({project_type:$('projectType').value}));
  function applyBudget(event){
    editingBudget=event.type==='input';
    try{change({cost_millions:Number($('budget').value)});}
    catch(error){$('budget').setCustomValidity(error.message);$('budget').setAttribute('aria-invalid','true');$('formStatus').textContent='Budget not applied: '+error.message+' Results still use the last valid budget.';if(event.type==='change')$('budget').reportValidity();}
    finally{editingBudget=false;}
  }
  $('budget').addEventListener('input',applyBudget);
  $('budget').addEventListener('change',applyBudget);
  $('coordinateForm').addEventListener('submit',event=>{event.preventDefault();try{change({longitude:Number($('longitude').value),latitude:Number($('latitude').value)});}catch(error){$('formStatus').textContent=error.message+' The previous location is unchanged.';sceneStatus({message:error.message});}});
  $('resetProposal').addEventListener('click',reset);
  $('resetView').addEventListener('click',()=>scene?.reset());
  $('exportScenario').addEventListener('click',()=>{
    const blob=new Blob([JSON.stringify({schema:'place-lab-scenario-v1',exported_at:new Date().toISOString(),source:data.source_label,...latest,decision_details:decisionExport(latest,model,history,$('historyProject').value,$('topicMeasure').value)},null,2)],{type:'application/json'});
    const url=URL.createObjectURL(blob),link=document.createElement('a');link.href=url;link.download='place-lab-scenario.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);$('exportStatus').textContent='Exported the profile, model result, chart data, assumptions, and historical topic evidence.';
  });
  render();
  const tools=agentTools.createPlaceTools({getCatalog:catalog,onTool});
  // Explicit adapter for browser integrations, plus native WebMCP when supported.
  Object.defineProperty(window,'placeLab',{value:Object.freeze({version:'place-tools-v1',tools:tools.map(({execute,...definition})=>definition),async call(name,args={}){const tool=tools.find(t=>t.name===name);return tool?tool.execute(args):{ok:false,error:'Unknown Place Lab tool.'};}}),configurable:true});
  agentTools.registerPlaceTools(document.modelContext || navigator.modelContext,tools).catch(()=>{/* Optional browser integration must never block human controls. */});
  $('buildStatus').textContent=`5 metros · ${number(data.cities.reduce((sum,c)=>sum+c.businesses.length,0))} mapped inventory records`;
  try {
    $('scene').replaceChildren();
    scene=await createPlaceMap({container:$('scene'),onPick:point=>{try{change({longitude:point.longitude,latitude:point.latitude});}catch(error){sceneStatus({message:error.message});$('formStatus').textContent=error.message+' The previous location is unchanged.';}},onStatus:sceneStatus});
    render();scene.focusSelection?.();
  }catch(error){sceneStatus({mode:'desktop',message:'The map is unavailable here. Use the location controls to keep exploring. '+error.message});}
  $('zoomIn').addEventListener('click',()=>scene?.zoomIn());
  $('zoomOut').addEventListener('click',()=>scene?.zoomOut());
  $('focusLocation').addEventListener('click',()=>scene?.focusSelection?.());
  window.addEventListener('pagehide',()=>{scene?.dispose();});
}
init().catch(error=>{$('formStatus').textContent='Place Lab could not load its local data. '+error.message;$('buildStatus').textContent='Data unavailable';$('sceneStatus').textContent='Run the documented build, then serve the web directory over HTTP.';});
