import {COMBINED_VIEWS,combinedEvidence,FOCUSES,areaAt,areaAnchor,areaValue,areaColor,areaTextColor,formatAreaValue} from './place_area_math.mjs';
import {createAreaExplorer} from './place_area_ui.js';
import {createPlaceMap} from './place_map.js';
import core from './place_core.cjs';
import {createPlaceTools,registerPlaceTools,TOOLKIT_VERSION} from './place_tools.mjs';
import {createNavigator} from './place_navigator.js';
import {ZIP_MEASURES} from './place_measures.mjs';
import {renderHistory} from './place_charts.js';
import {mountZipReport} from './place_report_view.tsx';
import {initTerms} from './place_term_dialog.tsx';
import {createPanelStore,mountPanel} from './place_panel.tsx';

const $=id=>document.getElementById(id);
const panel=createPanelStore({cities:[],cityLabel:'Loading…',city:null,zips:[],zip:null,focus:'activity',economic:'income',landmarks:[],landmark:null,projectTypes:[],projectType:null,budget:25,budgetError:null,basemap:'streets',showBusinesses:false,longitude:'',latitude:'',formStatus:'',locationAdjustment:'',basemapStatus:'Loading street detail…',sceneStatus:'Map loading.',selectionLabel:'',card:null,area:null,legend:null});
const number=(n, digits=0)=>Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits}):'—';
let renderZipReport=()=>{}, nav, anchorCache={}, highlightedMeasure=null, reportState={kind:'all',project_id:null,chart:'engagement'}, findings=null, areaData, areaExplorer, data, model, mapData, history, state, initial, scene, latest, lastCity, editingBudget=false, relocation=null,selectedZip=null;
function locationTitle() {
  const project=data.projects.find(p=>p.id===state.project_id);
  return project?'Near '+project.name:`${number(state.latitude,4)}, ${number(state.longitude,4)}`;
}
function selectZip(zip) {
  const geometry=mapData.cities.find(c=>c.id===state.city);
  const feature=geometry.features.find(f=>f.properties.zip===zip);
  if(!feature)return;
  const [longitude,latitude]=areaAnchor(feature);
  // ZIP evidence remains useful even when its fixed sample has no reviews.
  state=core.updateProposal(state,{longitude,latitude},data,{allowEmptyProfile:true});
  selectedZip=zip;relocation=null;render();
  sceneStatus(`Selected ZIP ${zip}. The highlighted boundary is the project area.`);
}
function renderProjectCard(focus) {
  if(!latest)return;
  const geometry=mapData.cities.find(c=>c.id===state.city);
  const zip=areaAt([state.longitude,state.latitude],geometry.features);
  const area=areaData.cities.find(c=>c.id===state.city).areas.find(a=>a.zip===zip);
  const value=areaValue(area,focus),spec=FOCUSES[focus];
  const isCombined=!!COMBINED_VIEWS[focus];
  const signalColor=focus==='none'?'#929d9b':areaColor(value,focus);
  const opportunities={
    combined:'Compare these historical signals when deciding where to investigate further. Their overlap does not establish a cause or predict the benefit of a project.',
    activity:'Explore public space and connections that help people reach nearby businesses.',
    income:'Explore affordable public amenities and connections with residents; prioritize who benefits and whether access remains affordable.',
    poverty:'Explore affordable public amenities and connections with residents; prioritize who benefits and whether access remains affordable.',
    decline:'Explore whether better public space or connections could support local activity. Check the causes of any decline with local businesses.',
    experience:'Use the review evidence to investigate local experiences and shape public-realm improvements with residents.',
    access:'Investigate the access and parking reviews, then assess walking, transit and accessibility improvements. Mentions include praise and complaints.',
    none:'Choose a focus to connect this project with the existing area analysis.'
  };
  const focusTitles={combined:'Poverty + activity',activity:'Business engagement',income:'Household income',poverty:'Poverty rate',decline:'Declining activity',experience:'Worsening experiences',access:'Access concerns',none:'Area overview'};
  panel.set({card:{
    title:`${COMBINED_VIEWS[focus]?.title??focusTitles[focus]}${zip?' · ZIP '+zip:''}`,
    meta:`${data.cities.find(c=>c.id===state.city).label} · whole-ZIP historical evidence`,
    signal:focus==='none'?number(area?.business_inventory):formatAreaValue(value,focus),
    signalColor:areaTextColor(value,focus),signalBorder:signalColor,combined:isCombined,
    combinedValues:isCombined?combinedEvidence(area,focus).map(({label,value,period})=>({label,value,period})):[],
    signalLabel:focus==='none'?'Yelp listings in the ZIP':`${spec.title}${spec.unit?" · "+spec.unit:""} · ${spec.period}`,
    opportunity:(focus!=='none'&&value===null?'This area has limited evidence for this focus. ':'')+(isCombined?opportunities.combined:opportunities[focus]),
    reach:`${number(area?.business_inventory)} Yelp listings and ${number(area?.late?.reviews)} reviews in 2019–2021 across ZIP ${zip}. These describe what happened, not what a new project would do.`,
    move:relocation?.distance_meters>0?`Marker moved ${number(relocation.distance_meters/1000,2)} km to a nearby data-supported candidate. This card describes the marker location.`:''
  }});
  renderZipReport({zip,area,city:areaData.cities.find(c=>c.id===state.city),cityLabel:data.cities.find(c=>c.id===state.city).label});
}
function render() {
  latest=core.inspectProposal(state,data,model);

  if(relocation)latest.map_selection=relocation;
  const {profile,result}=latest;
  const city=data.cities.find(c=>c.id===state.city);
  panel.set({cityLabel:city.label,city:state.city,landmark:state.project_id||null,
    longitude:state.longitude.toFixed(6),latitude:state.latitude.toFixed(6),projectType:state.project_type,budget:state.cost_millions,budgetError:null,
    selectionLabel:selectedZip?'ZIP '+selectedZip+' · selected project area':locationTitle(),
    formStatus:state.project_id?`Showing ZIP ${selectedZip??''} around ${data.projects.find(p=>p.id===state.project_id)?.name}.`:'',
    locationAdjustment:relocation ? (relocation.distance_meters > 0 ? `Moved ${number(relocation.distance_meters/1000,2)} km from your click to the nearest ${relocation.estimate_available?'model-supported':'reviewed-business'} candidate in this city. The marker, counts and charts describe the selected point.` : 'Showing measured data at your click.') + (relocation.estimate_available?'':' No supported estimate is available at this budget in this city. See the explanation below.') : ''});
  if(scene) {
    if(lastCity!==state.city) { const geometry=mapData.cities.find(c=>c.id===state.city);scene.setCity({...city,...geometry,projects:data.projects.filter(p=>p.city_id===city.id)});lastCity=state.city; }
    scene.setSelection({longitude:state.longitude,latitude:state.latitude,radiusMeters:500,zip:selectedZip});
    scene.setMetrics?.({title:locationTitle(),ce:result.estimate?.ce ?? null,costMillions:state.cost_millions,businesses:profile.baseline_reviewed,subtitle:'2018–2019 baseline · two-post-year proxy'});
  }
  areaExplorer?.update();
  if(areaExplorer)latest.area_exploration={...areaExplorer.snapshot(),selection_level:selectedZip?'zip':'point',project_zip:selectedZip};
}
function change(changes) {
  const locationChanged=['city','project_id','longitude','latitude'].some(key=>changes[key]!==undefined);
  const next=core.updateProposal(state,changes,data,{allowEmptyProfile:Boolean(selectedZip)&&!locationChanged});
  if(['city','project_id','longitude','latitude'].some(key=>changes[key]!==undefined)){relocation=null;selectedZip=null;}
  state=next;render();return latest;
}
function reset(){relocation=null;state={...initial};selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));scene?.reset();}
function sceneStatus(status) {
  panel.set({sceneStatus:typeof status==='string'?status:status.message||''});
}
// The page's side of the agent tools: what is on screen, and actions that only change the view.
function setFocusKey(focus){
  if(focus==='income'||focus==='poverty')panel.set({focus:'income',economic:focus});else panel.set({focus});
  areaExplorer.update();
}
const agentView={
  current(){const v=panel.get();return {section:nav.section(),city:state.city,zip:selectedZip,focus:v.focus==='income'?v.economic:v.focus,measure:highlightedMeasure,past_projects:{...reportState}};},
  showOnMap({city,zip,focus}){
    if(city&&city!==state.city){change({city});if(!zip)selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));}
    if(focus)setFocusKey(focus);
    if(zip){highlightedMeasure=null;areaExplorer.selectArea(zip);}
  },
  showPastProjects(detail){
    const clean=Object.fromEntries(Object.entries(detail).filter(([,v])=>v!=null));
    reportState={...reportState,...clean};
    window.dispatchEvent(new CustomEvent('place:past-projects',{detail:clean}));
    if(clean.chart)nav.focusItem('#project-charts','project_charts');
    else if(clean.project_id)nav.focusItem(`[data-project="${clean.project_id}"]`,'past_projects');
    else nav.goTo('past_projects');
  },
  goTo(section){if(section!=='zip_profile')highlightedMeasure=null;nav.goTo(section);},
  highlightMeasure(key){
    highlightedMeasure=key;
    const m=ZIP_MEASURES.find(m=>m.key===key);
    if(m?.focus)setFocusKey(m.focus);
    nav.focusItem(`[data-measure="${key}"]`,'zip_profile');
  },
  zoom(direction){direction==='in'?scene?.zoomIn():scene?.zoomOut();},
  anchors(cityId){
    if(!anchorCache[cityId])anchorCache[cityId]=Object.fromEntries(mapData.cities.find(c=>c.id===cityId).features.map(f=>[f.properties.zip,areaAnchor(f)]));
    return anchorCache[cityId];
  }
};
function initAgentTools(){
  nav=nav??createNavigator();
  window.addEventListener('place:report-state',event=>{reportState={...reportState,...event.detail};});
  // Every result is announced on screen and to assistive technology.
  const tools=createPlaceTools({data,areas:areaData,history,model,validation:findings?.text_validation??null,view:agentView})
    .map(tool=>({...tool,execute:async args=>{const result=await tool.execute(args);nav.announce(result.say);return result;}}));
  const webmcp={status:'checking',api:null,error:null};
  Object.defineProperty(window,'placeLab',{value:Object.freeze({version:TOOLKIT_VERSION,webmcp,tools:tools.map(({execute,...definition})=>definition),
    async call(name,args={}){const tool=tools.find(t=>t.name===name);return tool?tool.execute(args):{ok:false,error:`Unknown tool "${name}".`,valid_values:tools.map(t=>t.name)};}}),configurable:true});
  // WebMCP is optional: report whether the browser offered it, and why registration failed if it did.
  const context=document.modelContext??navigator.modelContext;
  webmcp.api=document.modelContext?'document.modelContext':navigator.modelContext?'navigator.modelContext':null;
  if(!context){webmcp.status='unavailable';console.info(`Place Lab: ${tools.length} agent tools are available as window.placeLab. WebMCP is not enabled in this browser, so they are not registered with it (enable chrome://flags "WebMCP for testing" and relaunch).`);}
  else registerPlaceTools(context,tools)
    .then(ok=>{webmcp.status=ok?'registered':'unsupported';console.info(`Place Lab: ${ok?`registered ${tools.length} tools with ${webmcp.api}`:`${webmcp.api} has no registerTool or provideContext`}.`);})
    .catch(error=>{webmcp.status='failed';webmcp.error=String(error);console.warn('Place Lab: WebMCP registration failed.',error);});
}
async function init() {
  nav=createNavigator();
  const reselect=()=>selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));
  const guard=fn=>(...args)=>{try{fn(...args);}catch(error){panel.set({formStatus:error.message+' The previous location is unchanged.'});sceneStatus({message:error.message});}};
  mountPanel($('panelRoot'),panel,{
    setCity:guard(city=>{change({city});reselect();}),
    setZip:zip=>areaExplorer.selectArea(zip),
    setFocus:focus=>{panel.set({focus});areaExplorer.update();},
    setEconomic:economic=>{panel.set({economic});areaExplorer.update();},
    setLandmark:guard(id=>{if(id!=='custom'){change({project_id:id});reselect();}}),
    setProjectType:project_type=>change({project_type}),
    // Typing applies valid budgets immediately; an invalid entry reverts to the last valid budget on blur.
    setBudget:(value,commit)=>{try{change({cost_millions:Number(value)});}catch(error){panel.set({budgetError:commit?null:error.message,formStatus:'Budget not applied: '+error.message+' Results still use the last valid budget.'});}},
    setCoordinates:guard((longitude,latitude)=>change({longitude,latitude})),
    reset,
    zoomIn:()=>scene?.zoomIn(),zoomOut:()=>scene?.zoomOut(),cityView:()=>scene?.reset(),focusSelection:()=>scene?.focusSelection?.(),
    focusArea:()=>areaExplorer.focusArea(),
    setBasemap:basemap=>{panel.set({basemap});scene?.setBasemap(basemap);},
    setBusinesses:showBusinesses=>{panel.set({showBusinesses});scene?.setBusinesses(showBusinesses);}
  });
  const assets=await Promise.all(['place-data.json','place-map.json','place-model.json','place-history.json','place-areas.json'].map(async path=>{const r=await fetch(path);if(!r.ok)throw new Error('Missing local asset: '+path);return r.json();}));
  [data,mapData,model,history,areaData]=assets;
  // Text-validation metrics feed the tools' reliability notes; the page works without them.
  findings=await fetch('findings-data.json').then(r=>r.ok?r.json():null).catch(()=>null);
  const pilot=data.projects.find(p=>p.id==='the-rail-park');
  initial={city:pilot.city_id,longitude:pilot.center[0],latitude:pilot.center[1],project_id:pilot.id,project_type:'Civic plaza / transit access',cost_millions:25};state={...initial};
  areaExplorer=createAreaExplorer({areaData,mapData,store:panel,getState:()=>state,getScene:()=>scene,onChange:renderProjectCard,onSelect:selectZip});
  renderZipReport=mountZipReport($('reportRoot'),{history,model,projects:data.projects,onHistory:id=>renderHistory(history,id)});
  initTerms($('termRoot'));
  panel.set({cities:data.cities.map(({id,label})=>({id,label})),
    landmarks:data.projects.filter(p=>p.city_id).map(p=>({id:p.id,label:`${p.name} · ${p.city_label}`})),
    projectTypes:[...new Set([...core.TYPES,...data.projects.map(p=>p.project_type)])]});
  selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));
  initAgentTools();
  $('buildStatus').textContent=`5 metros · ${number(data.cities.reduce((sum,c)=>sum+c.businesses.length,0))} mapped inventory records`;
  try {
    $('scene').replaceChildren();
    scene=await createPlaceMap({container:$('scene'),getLeftInset:()=>$('proposalControls').getBoundingClientRect().right-$('scene').getBoundingClientRect().left+24,onPick:point=>{try{const geometry=mapData.cities.find(c=>c.id===state.city);const zip=areaAt([point.longitude,point.latitude],geometry.features);if(zip){selectZip(zip);}else{panel.set({card:{...panel.get().card,move:'Choose a mapped ZIP area. Your current ZIP remains selected.'}});sceneStatus('No mapped ZIP at this click. Current selection retained.');}}catch(error){sceneStatus({message:error.message});panel.set({formStatus:error.message+' The previous location is unchanged.'});}},onStatus:sceneStatus,onBasemapStatus:basemapStatus=>panel.set({basemapStatus})});
    render();scene.reset();
  }catch(error){sceneStatus({mode:'desktop',message:'The map is unavailable here. Use the location controls to keep exploring. '+error.message});}
  window.addEventListener('pagehide',()=>{scene?.dispose();});
}
init().catch(error=>{panel.set({formStatus:'Place Lab could not load its local data. '+error.message,sceneStatus:'Run the documented build, then serve the web directory over HTTP.'});$('buildStatus').textContent='Data unavailable';});
