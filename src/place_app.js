import {PERIODS,applyPeriodLabels,COMBINED_VIEWS,combinedEvidence,FOCUSES,areaAt,areaAnchor,areaValue,areaColor,areaTextColor,formatAreaValue} from './place_area_math.mjs';
import {createAreaExplorer} from './place_area_ui.js';
import {createPlaceMap} from './place_map.js';
import core from './place_core.cjs';
import {createPlaceTools,TOOLKIT_VERSION} from './place_tools.mjs';
import {createNavigator} from './place_navigator.js';
import {connectPlaceBridge} from './place_bridge.mjs';
import {ZIP_MEASURES} from './place_measures.mjs';
import {renderHistory} from './place_charts.js';
import {mountZipReport} from './place_report_view.tsx';
import {initTerms} from './place_term_dialog.tsx';
import {createPanelStore,mountPanel} from './place_panel.tsx';
import {DEFAULT_TIME,clampTimeSetting,applyTime,isDefault,periodCount,periodLabel,parsePeriod,windows,zipSeries} from './place_timeline.mjs';
import {mountToolbar} from './place_toolbar.tsx';

const $=id=>document.getElementById(id);
const panel=createPanelStore({cities:[],cityLabel:'Loading…',city:null,zips:[],zip:null,focus:'activity',economic:'income',landmarks:[],landmark:null,projectTypes:[],projectType:null,budget:25,budgetError:null,basemap:'streets',showBusinesses:false,longitude:'',latitude:'',formStatus:'',locationAdjustment:'',basemapStatus:'Loading street detail…',sceneStatus:'Map loading.',selectionLabel:'',card:null,area:null,legend:null});
const timeStore=createPanelStore({ready:false});
const number=(n, digits=0)=>Number.isFinite(n)?n.toLocaleString('en-US',{maximumFractionDigits:digits,minimumFractionDigits:digits}):'—';
let renderZipReport=()=>{}, nav, anchorCache={}, highlightedMeasure=null, reportState={kind:'all',project_id:null,chart:'engagement'}, findings=null, areaData, areaExplorer, data, model, mapData, history, state, initial, scene, latest, lastCity, editingBudget=false, relocation=null,selectedZip=null,timeline=null,timeSetting={...DEFAULT_TIME},playTimer=null;
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
  const signalColor=focus==='none'?'var(--c-929d9b)':areaColor(value,focus);
  const opportunities={
    combined:'Use these signals together to decide where to look closer. Where they overlap tells you nothing about cause, and nothing about what a project would deliver.',
    activity:'Look at public space and connections that help people reach nearby businesses.',
    income:'Talk with residents about affordable amenities and connections. Ask who benefits and whether access stays affordable.',
    poverty:'Talk with residents about affordable amenities and connections. Ask who benefits and whether access stays affordable.',
    decline:'Ask local businesses why activity fell before deciding whether public space or connections would help.',
    experience:'Read the reviews behind this, then work out public-space fixes with residents.',
    access:'Read the access and parking reviews, then check walking, transit and accessibility on the ground. Mentions count praise and complaints alike.',
    none:'Choose a focus to color the map.'
  };
  const focusTitles={combined:'Poverty + activity',activity:'Business engagement',income:'Household income',poverty:'Poverty rate',decline:'Declining activity',experience:'Worsening experiences',access:'Access concerns',none:'Area overview'};
  panel.set({card:{
    title:`${COMBINED_VIEWS[focus]?.title??focusTitles[focus]}${zip?' · ZIP '+zip:''}`,
    meta:`${data.cities.find(c=>c.id===state.city).label} · whole-ZIP historical evidence`,
    signal:focus==='none'?number(area?.business_inventory):formatAreaValue(value,focus),
    signalColor:areaTextColor(value,focus),signalBorder:signalColor,combined:isCombined,
    combinedValues:isCombined?combinedEvidence(area,focus).map(({label,value,period})=>({label,value,period})):[],
    signalLabel:focus==='none'?'Yelp listings in the ZIP':`${spec.title}${spec.unit?" · "+spec.unit:""} · ${spec.period}`,
    opportunity:(focus!=='none'&&value===null?'This ZIP has too little data for this focus. ':'')+(isCombined?opportunities.combined:opportunities[focus]),
    reach:`${number(area?.business_inventory)} Yelp listings and ${number(area?.late?.reviews)} reviews in ${PERIODS.level} across ZIP ${zip}. These show what happened. They do not predict what a new project would do.`,
    move:relocation?.distance_meters>0?`We moved the marker ${number(relocation.distance_meters/1000,2)} km to the nearest spot with enough data. This card describes the new spot.`:''
  }});
  renderZipReport({zip,area,city:areaData.cities.find(c=>c.id===state.city),cityLabel:data.cities.find(c=>c.id===state.city).label,time:zip&&timeline?zipTime(zip):null});
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
  if(timeline)publishTime();
  areaExplorer?.update();
  if(areaExplorer)latest.area_exploration={...areaExplorer.snapshot(),selection_level:selectedZip?'zip':'point',project_zip:selectedZip};
}
function change(changes) {
  const locationChanged=['city','project_id','longitude','latitude'].some(key=>changes[key]!==undefined);
  const next=core.updateProposal(state,changes,data,{allowEmptyProfile:Boolean(selectedZip)&&!locationChanged});
  if(['city','project_id','longitude','latitude'].some(key=>changes[key]!==undefined)){relocation=null;selectedZip=null;}
  state=next;render();return latest;
}
// Map timeline: every review-based ZIP measure is rebuilt for the chosen periods, in place,
// so the map, the ZIP profile and the agent tools always describe the same periods.
const monthIndex=text=>{const [y,m]=text.split('-').map(Number);const [y0,m0]=timeline.start.split('-').map(Number);return (y-y0)*12+(m||1)-m0;};
function clampTime(s){return clampTimeSetting(timeline,s);}

function cityMarkers(u,n){
  return history.projects.filter(p=>data.projects.find(d=>d.id===p.id)?.city_id===state.city)
    .map(p=>({id:p.id,name:p.project,opening:p.opening.slice(0,7),index:Math.floor(monthIndex(p.opening)/u)})).filter(m=>m.index>=0&&m.index<n);
}
// Series and shaded periods for the ZIP profile's time chart.
function zipTime(zip){
  const s=timeSetting,u=s.grain==='quarter'?3:1,n=periodCount(timeline,s.grain),{level,base}=windows(timeline,s);
  const toPeriods=([a,b],kind)=>a>=0&&b<timeline.months?[[Math.floor(a/u),Math.floor(b/u),kind]]:[];
  return {series:zipSeries(timeline,state.city,zip,s),shade:[...toPeriods(base,'base'),...toPeriods(level,'level')],markers:cityMarkers(u,n),
    covidIndex:Math.floor(monthIndex('2020-03')/u),grain:s.grain,smooth:s.smooth};
}
function publishTime(){
  const s=timeSetting,n=periodCount(timeline,s.grain),u=s.grain==='quarter'?3:1;
  const markers=cityMarkers(u,n);
  timeStore.set({ready:true,setting:s,count:n,periods:Array.from({length:n},(_,i)=>periodLabel(timeline,s.grain,i)),text:areaData.time.labels,
    markers,covidIndex:Math.floor(monthIndex('2020-03')/u),playing:!!playTimer,isDefault:isDefault(s),minAt:s.grain==='month'?s.smooth-1:0});
}
function setTime(patch){
  if(!timeline)return null;
  timeSetting=clampTime({...timeSetting,...patch});
  const t=applyTime(areaData,timeline,timeSetting);
  applyPeriodLabels({level:t.labels.level,base:t.labels.base,change:t.labels.change});
  publishTime();areaExplorer?.update();
  return {setting:{...timeSetting},labels:{...t.labels}};
}
function setGrain(grain){
  const s=timeSetting;if(grain===s.grain)return setTime({});
  return setTime(grain==='month'?{grain,at:s.at*3+2,from:s.from*3,to:s.to*3,length:s.length*3,smooth:3}
    :{grain,at:Math.floor(s.at/3),from:Math.floor(s.from/3),to:Math.floor(s.to/3),length:Math.max(1,Math.round(s.length/3))});
}
function stopPlay(){if(playTimer){clearInterval(playTimer);playTimer=null;publishTime();}}
function togglePlay(){
  if(playTimer)return stopPlay();
  if(timeSetting.at>=periodCount(timeline,timeSetting.grain)-1)setTime({at:0});
  playTimer=setInterval(()=>{if(timeSetting.at>=periodCount(timeline,timeSetting.grain)-1)stopPlay();else setTime({at:timeSetting.at+1});},800);
  publishTime();
}
// Compare equal periods either side of a project's opening, up to two years each, and select its ZIP.
function projectStart(id){
  const p=history.projects.find(p=>p.id===id),u=timeSetting.grain==='quarter'?3:1,n=periodCount(timeline,timeSetting.grain);
  const open=Math.floor(monthIndex(p.opening)/u),length=Math.max(1,Math.min(24/u,open,n-1-open));
  stopPlay();
  if(data.projects.find(d=>d.id===id)?.city_id&&state.project_id!==id){change({project_id:id});selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));}
  return setTime({mode:'compare',length,from:open-length,to:open+1});
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
  current(){const v=panel.get();return {section:nav.section(),city:state.city,zip:selectedZip,focus:v.focus==='income'?v.economic:v.focus,measure:highlightedMeasure,past_projects:{...reportState},map_period:areaData.time?.labels??null};},
  showOnMap({city,zip,focus}){
    if(city&&city!==state.city){change({city});if(!zip)selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));}
    if(focus)setFocusKey(focus);
    if(zip){highlightedMeasure=null;areaExplorer.selectArea(zip);}
  },
  time(){return timeline?{setting:{...timeSetting},labels:{...areaData.time.labels},periods:periodCount(timeline,timeSetting.grain),
    first:periodLabel(timeline,timeSetting.grain,0),last:periodLabel(timeline,timeSetting.grain,periodCount(timeline,timeSetting.grain)-1)}:null;},
  parsePeriod(grain,text){return timeline?parsePeriod(timeline,grain,text):null;},
  setTime(patch){stopPlay();if(patch.grain&&patch.grain!==timeSetting.grain){setGrain(patch.grain);const {grain,...rest}=patch;patch=rest;}return setTime(patch);},
  startAtProject(id){return projectStart(id);},
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
  Object.defineProperty(window,'placeLab',{value:Object.freeze({version:TOOLKIT_VERSION,tools:tools.map(({execute,...definition})=>definition),
    async call(name,args={}){const tool=tools.find(t=>t.name===name);return tool?tool.execute(args):{ok:false,error:`Unknown tool "${name}".`,valid_values:tools.map(t=>t.name)};}}),configurable:true});

}
async function init() {
  nav=createNavigator();
  const reselect=()=>selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));
  const guard=fn=>(...args)=>{try{fn(...args);}catch(error){panel.set({formStatus:error.message+' The map stays where it was.'});sceneStatus({message:error.message});}};
  const panelActions={
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
  };
  mountPanel($('panelRoot'),panel,panelActions);
  // Sections scrolled into view must clear the sticky header.
  const header=$('appHeader');
  new ResizeObserver(()=>document.documentElement.style.setProperty('--header-h',header.offsetHeight+'px')).observe(header);
  const assets=await Promise.all(['place-data.json','place-map.json','place-model.json','place-history.json','place-areas.json'].map(async path=>{const r=await fetch(path);if(!r.ok)throw new Error('Missing local asset: '+path);return r.json();}));
  [data,mapData,model,history,areaData]=assets;
  // Text-validation metrics feed the tools' reliability notes; the page works without them.
  findings=await fetch('findings-data.json').then(r=>r.ok?r.json():null).catch(()=>null);
  // The timeline is optional: without it the map keeps the published 2012–14 vs 2019–21 comparison.
  timeline=await fetch('place-timeline.json').then(r=>r.ok?r.json():null).catch(()=>null);
  const pilot=data.projects.find(p=>p.id==='the-rail-park');
  initial={city:pilot.city_id,longitude:pilot.center[0],latitude:pilot.center[1],project_id:pilot.id,project_type:'Civic plaza / transit access',cost_millions:25};state={...initial};
  areaExplorer=createAreaExplorer({areaData,mapData,store:panel,getState:()=>state,getScene:()=>scene,onChange:renderProjectCard,onSelect:selectZip});
  renderZipReport=mountZipReport($('reportRoot'),{history,model,projects:data.projects,onHistory:id=>renderHistory(history,id)});
  initTerms($('termRoot'));
  const timeActions=timeline?{setTime:patch=>{stopPlay();setTime(patch);},setMode:mode=>{stopPlay();setTime({mode});},setGrain:grain=>{stopPlay();setGrain(grain);},
    togglePlay,projectStart,openProject:id=>agentView.showPastProjects({project_id:id}),reset:()=>{stopPlay();setTime({...DEFAULT_TIME});}}:null;
  if(timeline)applyTime(areaData,timeline,timeSetting);
  mountToolbar($('filtersRoot'),$('toolbarRoot'),panel,panelActions,timeline?timeStore:null,timeActions);
  panel.set({cities:data.cities.map(({id,label})=>({id,label})),
    landmarks:data.projects.filter(p=>p.city_id).map(p=>({id:p.id,label:`${p.name} · ${p.city_label}`})),
    projectTypes:[...new Set([...core.TYPES,...data.projects.map(p=>p.project_type)])]});
  selectZip(areaAt([state.longitude,state.latitude],mapData.cities.find(c=>c.id===state.city).features));
  initAgentTools();
  $('buildStatus').textContent=`5 metros · ${number(data.cities.reduce((sum,c)=>sum+c.businesses.length,0))} mapped inventory records`;
  try {
    $('scene').replaceChildren();
    scene=await createPlaceMap({container:$('scene'),getLeftInset:()=>$('proposalControls').getBoundingClientRect().right-$('scene').getBoundingClientRect().left+24,onPick:point=>{try{const geometry=mapData.cities.find(c=>c.id===state.city);const zip=areaAt([point.longitude,point.latitude],geometry.features);if(zip){selectZip(zip);}else{panel.set({card:{...panel.get().card,move:'Choose a mapped ZIP area. Your current ZIP remains selected.'}});sceneStatus('No mapped ZIP at this click. Current selection retained.');}}catch(error){sceneStatus({message:error.message});panel.set({formStatus:error.message+' The map stays where it was.'});}},onStatus:sceneStatus,onBasemapStatus:basemapStatus=>panel.set({basemapStatus})});
    render();scene.reset();
  }catch(error){sceneStatus({mode:'desktop',message:'The map can\'t load here. The controls on the left still work. '+error.message});}
  connectPlaceBridge({call:window.placeLab.call,current:()=>({...agentView.current(),time:agentView.time()}),subscribe:fn=>{const a=panel.subscribe(fn),b=timeStore.subscribe(fn);return ()=>{a();b();};}});
  window.addEventListener('pagehide',()=>{scene?.dispose();});
}
init().catch(error=>{panel.set({formStatus:'Place Lab couldn\'t load its data. '+error.message,sceneStatus:'Run the build in the README, then serve the web folder over HTTP.'});$('buildStatus').textContent='Data unavailable';});
