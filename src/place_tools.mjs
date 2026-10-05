// Place Lab agent tools: the same evidence a person sees, as structured tool calls,
// designed for voice and chat agents. Exposed as window.placeLab and registered with
// WebMCP (document.modelContext; navigator.modelContext before Chrome 150) when supported. Lookup tools are
// read-only; navigation and show_* tools only change what is on screen. Every result
// carries `say`, a short sentence an agent can read aloud. Nothing here forecasts a
// new project or sends data anywhere.
import {ZIP_MEASURES,zipProfile} from './place_measures.mjs';
import {FOCUSES,COMBINED_VIEWS} from './place_area_math.mjs';
import {DEFAULT_TIME} from './place_timeline.mjs';
import {FAMILIES,OUTCOMES,projectEffects,familySummary,leaveOneOut} from './place_projection.mjs';
import {GLOSSARY,CATEGORIES} from './place_glossary.mjs';
import {SECTIONS,CHART_TABS,COMPASS,stepIndex,neighborZip} from './place_navigation.mjs';
import insights from './place_insights.cjs';

export const TOOLKIT_VERSION='place-lab-tools-v2';
const KINDS=['all',...Object.keys(FAMILIES)];
const FOCUS_KEYS=Object.keys(FOCUSES);
const MEASURE_KEYS=ZIP_MEASURES.map(m=>m.key);
const SECTION_KEYS=SECTIONS.map(s=>s.key);
const CHART_KEYS=CHART_TABS.map(([k])=>k);
const OUTCOME_KEYS={activity:'engagement_change_pct',sentiment:'sentiment_change',access:'negative_access_change_pp',realm:'negative_public_space_change_pp'};
const OUTCOME_UNITS={activity:'% change in reviews, comparison-adjusted',sentiment:'VADER points, comparison-adjusted',access:'percentage points, comparison-adjusted',realm:'percentage points, comparison-adjusted'};
// Names people say aloud for the covered metros.
const CITY_ALIASES={philly:'philadelphia',phl:'philadelphia',tampa:'tampabay',stpete:'tampabay',stpetersburg:'tampabay',clearwater:'tampabay',nola:'neworleans',musiccity:'nashville',nash:'nashville'};
const CHART_OUTCOME={engagement:'activity',sentiment:'sentiment',access:'access',realm:'realm'};
const round=(v,d=3)=>Number.isFinite(v)?Number(v.toFixed(d)):null;
const ordinal=n=>n+(['th','st','nd','rd'][(n%100-20)%10]||['th','st','nd','rd'][n%100]||'th');
const READ={readOnlyHint:true,openWorldHint:false};
// consequentialHint is Chrome's WebMCP hint; the others are MCP's. View changes are harmless and reversible.
const VIEW={readOnlyHint:false,consequentialHint:false,destructiveHint:false,idempotentHint:false,openWorldHint:false};

class ToolError extends Error{constructor(message,hint,valid){super(message);this.hint=hint;this.valid_values=valid;}}

/**
 * view: the page's on-screen state and actions.
 *   current()                    -> {section, city, zip, focus, measure, past_projects:{kind, project_id, chart}}
 *   showOnMap({city, zip, focus}), showPastProjects({kind, project_id, chart}),
 *   goTo(section), highlightMeasure(key), zoom('in'|'out'), anchors(cityId) -> {zip: [lon, lat]}
 */
export function createPlaceTools({data,areas,history,model,validation=null,view}){
  const cityList=data.cities.map(c=>({id:c.id,label:c.label}));
  const rows=projectEffects(history,model.excluded_projects.map(p=>p.id));
  const kindCheck=leaveOneOut(rows);
  const cityLabel=id=>cityList.find(c=>c.id===id)?.label??id;

  function resolveCity(input){
    if(input==null||input==='')return null;
    const raw=String(input).toLowerCase().replace(/[^a-z]/g,''),key=CITY_ALIASES[raw]??raw;
    const city=cityList.find(c=>c.id.toLowerCase()===key||c.label.toLowerCase().replace(/[^a-z]/g,'')===key||c.label.toLowerCase().replace(/[^a-z]/g,'').startsWith(key));
    if(!city)throw new ToolError(`Unknown city "${input}".`,'Use a city id or label from get_place_lab_guide.',cityList.map(c=>c.id));
    return city;
  }
  const areasOf=city=>areas.cities.find(c=>c.id===city.id).areas;
  function resolveZip(zip,cityInput){
    const z=String(zip??'').trim();
    if(!/^\d{5}$/.test(z))throw new ToolError(`"${zip}" is not a five-digit ZIP.`,'Pass the ZIP as a string such as "19134".');
    const candidates=cityInput?[resolveCity(cityInput)]:cityList;
    const city=candidates.find(c=>areasOf(c).some(a=>a.zip===z));
    if(!city){
      const scope=cityInput?`in ${candidates[0].label}`:'in any covered city';
      throw new ToolError(`ZIP ${z} is not mapped ${scope}.`,'Use find_zips to list mapped ZIPs; coverage is limited to five metros.',cityInput?areasOf(candidates[0]).map(a=>a.zip).sort():undefined);
    }
    return {city,zip:z};
  }
  const project=id=>{
    const p=data.projects.find(p=>p.id===id);
    if(!p)throw new ToolError(`Unknown project "${id}".`,'Use a project id from get_place_lab_guide.',data.projects.map(p=>p.id));
    return p;
  };
  const kindOf=id=>rows.find(r=>r.id===id)?.family??null;
  const kindLabel=k=>k==='all'?'all projects':FAMILIES[k].label;
  const definition=term=>GLOSSARY[term]?{definition:GLOSSARY[term].definition,caution:GLOSSARY[term].caution??null}:{};

  function profileOf(city,zip){
    return zipProfile(areasOf(city),zip).map(r=>({
      measure:r.measure.key,label:r.measure.label,value:round(r.value),display:r.value===null?'Limited data':r.measure.format(r.value),
      unit:r.measure.unit,period:r.period,city_median:round(r.median),rank:r.rank,ranked_zips:r.compared,
      percentile:r.position===null?null:Math.round(100*r.position),limited_data:r.value===null,
      ...(r.moe!==null?{margin_of_error:r.moe}:{}),...definition(r.measure.term)}));
  }
  // One spoken sentence about a measure in a ZIP, e.g. "Business engagement: 876 reviews / km² / year, 6th of 48 in Philadelphia (city median 52)."
  function speakMeasure(city,zip,key){
    const r=zipProfile(areasOf(city),zip).find(r=>r.measure.key===key);
    if(!r)return '';
    if(r.value===null)return `${r.measure.label} has limited data in ZIP ${zip}.`;
    const unit=/%|\$|km²/.test(r.measure.format(r.value))?'':' '+r.measure.unit;
    return `${r.measure.label}: ${r.measure.format(r.value)}${unit}, ${ordinal(r.rank)} of ${r.compared} in ${city.label} (city median ${r.measure.format(r.median)}).`;
  }
  function reliability(){
    const v=validation;
    const status=v?.labels?.status??'Text measures have not been validated in this build.';
    const neg=v?.negative_area,pol=v?.vader_polarity;
    return {
      [OUTCOME_KEYS.activity]:'Counts Yelp reviews, with no text labeling. It cannot see visits or sales.',
      [OUTCOME_KEYS.sentiment]:pol?`VADER agrees with clause labels ${Math.round(100*pol.accuracy)}% of the time (macro-F1 ${round(pol.macro_f1,2)}). ${status}`:status,
      [OUTCOME_KEYS.access]:neg?`Low reliability. Keyword rules found ${Math.round(100*neg.recall)}% of negative area comments, with precision ${round(neg.precision,2)}, so this undercounts complaints. ${status}`:status,
      [OUTCOME_KEYS.realm]:neg?`Low reliability. It uses the same rules as negative access, with recall ${round(neg.recall,2)}. ${status}`:status
    };
  }
  const changeOf=(r,key)=>key==='activity'?100*(Math.exp(r.effects[key])-1):r.effects[key];
  const changes=r=>Object.fromEntries(OUTCOMES.map(o=>[OUTCOME_KEYS[o.key],round(changeOf(r,o.key),o.key==='activity'?1:3)]));
  const fmtChange=(key,v)=>key==='activity'?`${v>0?'+':''}${Math.round(v)}%`:key==='sentiment'?`${v>0?'+':''}${v.toFixed(3)}`:`${v>0?'+':''}${v.toFixed(2)} points`;

  // A spoken summary of whatever the user is looking at.
  function describe(){
    const v=view.current(),city=resolveCity(v.city),past=v.past_projects??{kind:'all'};
    const section=SECTIONS.find(s=>s.key===v.section)??SECTIONS[0];
    let say;
    if(section.key==='map'||section.key==='zip_profile'){
      const focusMeasure=ZIP_MEASURES.find(m=>m.key===v.measure)??ZIP_MEASURES.find(m=>m.focus===v.focus)??ZIP_MEASURES.find(m=>m.key==='engagement');
      say=v.zip?`${section.label}: ZIP ${v.zip} in ${city.label}. ${speakMeasure(city,v.zip,focusMeasure.key)}`:`${section.label} of ${city.label}. No ZIP is selected.`;
    }else if(section.key==='past_projects'){
      const s=familySummary(rows,past.kind??'all');
      say=`Past projects, ${kindLabel(past.kind??'all')}: ${s.n} projects. Engagement improved near ${s.outcomes.activity.better} and sentiment near ${s.outcomes.sentiment.better}, compared with their surroundings.`;
    }else if(section.key==='project_charts'){
      const id=past.project_id??familySummary(rows,past.kind??'all').members[0]?.id,r=rows.find(r=>r.id===id),tab=CHART_TABS.find(([k])=>k===(past.chart??'engagement'));
      const key=CHART_OUTCOME[tab[0]];
      say=r?`${tab[1]} chart for ${r.project}.${key?` Compared with its surroundings, the change was ${fmtChange(key,changeOf(r,key))}.`:' It shows which topics people discussed more or less after opening.'}`:'Project charts.';
    }else say='Notes. Reviews come from Yelp\'s January 2022 archive, and income and poverty from ACS estimates. Everything here describes the past. Nothing forecasts.';
    return {section:section.key,left_right_moves:section.left_right,say,view:v};
  }

  const tools=[
    {name:'get_place_lab_guide',title:'What Place Lab covers and how to ask it',
      description:'Start here. Returns what Place Lab can and cannot answer, the covered cities, the ZIP measures with units, map focuses, page sections and how to navigate them, kinds of past project, the eleven past projects, and what is on screen now. Place Lab is historical: it describes what happened, never what a new project would do.',
      inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:READ,
      run:()=>({
        about:'Place Lab maps historical Yelp review activity and language with Census income and poverty for ZIPs in five metros, and shows what changed around eleven past public projects compared with their surrounding areas.',
        can_answer:['How a ZIP compares with others in its city on engagement, sentiment, access discussion, income and poverty','Which ZIPs rank highest or lowest on a measure, optionally filtered by others','What changed around past trails, parks, plazas and a streetcar line, project by project','What a term means and how it was calculated'],
        cannot_answer:['What a new project, budget or location would cause','Current conditions, because reviews end in January 2022 and income and poverty are 2007–2012 ACS estimates','Visits, sales, revenue or resident wellbeing','Areas outside the mapped ZIPs'],
        cities:cityList.map(c=>({...c,mapped_zips:areasOf(c).length})),
        zip_measures:ZIP_MEASURES.map(m=>({key:m.key,label:m.label,unit:m.unit,map_focus:m.focus??null})),
        map_focuses:FOCUS_KEYS.map(k=>({key:k,label:FOCUSES[k].label??FOCUSES[k].title,combined:!!COMBINED_VIEWS[k]})),
        page_sections:SECTIONS.map(s=>({key:s.key,label:s.label,left_right_moves:s.left_right})),
        navigation:'navigate up/down moves between sections, left/right steps within one, in/out zooms the map. move_to_neighbor goes to the adjacent ZIP north, south, east or west. go_to jumps to a section. describe_screen says what is showing.',
        project_kinds:KINDS.map(k=>({key:k,label:k==='all'?'All projects':FAMILIES[k].label,projects:k==='all'?rows.length:rows.filter(r=>r.family===k).length})),
        past_projects:data.projects.map(p=>({id:p.id,name:p.name,city:p.city_label,kind:kindOf(p.id),opened:history.projects.find(h=>h.id===p.id)?.opening??null,compared:!!kindOf(p.id)})),
        chart_tabs:CHART_TABS.map(([key,label])=>({key,label})),
        map_time:view.time?.()??null,
        time_note:'Review-based ZIP measures can describe any quarter or month from January 2012 to December 2021. Use set_map_time to change the period. Income and poverty stay at their ACS baseline.',
        current_view:view.current(),
        say:`Place Lab covers ${cityList.length} metros and ${data.projects.length} past projects, ${rows.length} with enough data to compare. Ask about a ZIP, rank ZIPs by a measure, or compare past projects.`})},

    {name:'describe_screen',title:'Say what is on screen',
      description:'Returns the section the user is looking at, the selected city and ZIP, the map focus, the past-projects filter and chart, and a spoken summary. Call after the user scrolls or asks "where am I?" or "what am I looking at?".',
      inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:READ,run:()=>describe()},

    {name:'navigate',title:'Move around the page like arrow keys',
      description:'Moves the user\'s view. up/down: previous or next page section (map, ZIP profile, past projects, project charts, notes), with smooth scrolling and focus. left/right: previous or next item inside the current section (map: neighboring ZIP west or east; ZIP profile: previous or next measure, and the map switches to it; past projects: previous or next kind of project; project charts: previous or next chart). in/out: zoom the map. Returns what is now on screen.',
      inputSchema:{type:'object',properties:{direction:{type:'string',enum:['up','down','left','right','in','out']},steps:{type:'integer',minimum:1,maximum:5,default:1}},required:['direction'],additionalProperties:false},annotations:VIEW,
      run:({direction,steps=1})=>{
        if(!['up','down','left','right','in','out'].includes(direction))throw new ToolError(`Unknown direction "${direction}".`,'Use up, down, left, right, in or out.',['up','down','left','right','in','out']);
        const n=Math.max(1,Math.min(5,Math.floor(steps))),sign=direction==='up'||direction==='left'?-1:1;
        if(direction==='in'||direction==='out'){for(let i=0;i<n;i++)view.zoom(direction);return {...describe(),say:`Zoomed ${direction}. `+describe().say};}
        const current=view.current();
        if(direction==='up'||direction==='down'){
          const index=SECTION_KEYS.indexOf(current.section),next=Math.max(0,Math.min(SECTION_KEYS.length-1,index+sign*n));
          if(next===index)return {...describe(),say:`Already at the ${direction==='up'?'top':'bottom'} of the page. `+describe().say};
          view.goTo(SECTION_KEYS[next]);
          return describe();
        }
        const section=current.section;
        if(section==='map'){
          let zip=current.zip;const anchors=view.anchors(current.city);
          for(let i=0;i<n&&zip;i++){const next=neighborZip(anchors,zip,sign<0?'west':'east');if(!next)break;zip=next;}
          if(!zip||zip===current.zip)return {...describe(),say:`There is no mapped ZIP further ${sign<0?'west':'east'}.`};
          view.showOnMap({city:current.city,zip});
          return describe();
        }
        if(section==='zip_profile'){
          const index=stepIndex(MEASURE_KEYS.length,MEASURE_KEYS.indexOf(current.measure),sign*n);
          view.highlightMeasure(MEASURE_KEYS[index]);
          return describe();
        }
        if(section==='past_projects'){
          const kind=KINDS[stepIndex(KINDS.length,KINDS.indexOf(current.past_projects?.kind??'all'),sign*n)];
          view.showPastProjects({kind});
          return describe();
        }
        if(section==='project_charts'){
          const chart=CHART_KEYS[stepIndex(CHART_KEYS.length,CHART_KEYS.indexOf(current.past_projects?.chart??'engagement'),sign*n)];
          view.showPastProjects({chart});
          return describe();
        }
        return {...describe(),say:'Nothing to step through here. Say up to go back to the charts.'};
      }},

    {name:'go_to',title:'Jump to a page section',
      description:'Scrolls smoothly to a section and moves focus to its heading: map, zip_profile, past_projects, project_charts or notes.',
      inputSchema:{type:'object',properties:{section:{type:'string',enum:SECTION_KEYS}},required:['section'],additionalProperties:false},annotations:VIEW,
      run:({section})=>{
        if(!SECTION_KEYS.includes(section))throw new ToolError(`Unknown section "${section}".`,'Use one of the listed sections.',SECTION_KEYS);
        view.goTo(section);return describe();
      }},

    {name:'move_to_neighbor',title:'Go to the adjacent ZIP',
      description:'Selects the mapped ZIP next to the current one in a compass direction (north, south, east or west), zooms the map to it and returns its headline numbers. Use for "what is next door?" or "go north".',
      inputSchema:{type:'object',properties:{direction:{type:'string',enum:Object.keys(COMPASS)}},required:['direction'],additionalProperties:false},annotations:VIEW,
      run:({direction})=>{
        if(!COMPASS[direction])throw new ToolError(`Unknown direction "${direction}".`,'Use north, south, east or west.',Object.keys(COMPASS));
        const current=view.current();
        if(!current.zip)throw new ToolError('No ZIP is selected.','Select a ZIP first with show_on_map.');
        const next=neighborZip(view.anchors(current.city),current.zip,direction);
        if(!next)return {...describe(),say:`There is no mapped ZIP to the ${direction} of ${current.zip}.`};
        view.showOnMap({city:current.city,zip:next});
        if(view.current().section!=='map')view.goTo('map');
        return {...describe(),moved_from:current.zip};
      }},

    {name:'get_zip_profile',title:'Profile one ZIP against its city',
      description:'Returns every ZIP measure for one ZIP: value, unit, period, city median, rank (1 = highest), percentile, and definition. "Limited data" means too few reviews, never zero. City is optional; it is found from the ZIP. Does not change the screen; use show_on_map to show it.',
      inputSchema:{type:'object',properties:{zip:{type:'string',pattern:'^\\d{5}$',description:'Five-digit ZIP, e.g. "19134".'},city:{type:'string',description:'Optional city id or label.'}},required:['zip'],additionalProperties:false},annotations:READ,
      run:({zip,city})=>{const r=resolveZip(zip,city);return {city:r.city.label,zip:r.zip,compared_with:`${areasOf(r.city).length} mapped ZIPs in ${r.city.label}`,measures:profileOf(r.city,r.zip),
        notes:['Review measures come from Yelp\'s January 2022 archive and cover Yelp-listed businesses only.','Income and poverty are older ACS estimates that describe residents. Reviewers may live anywhere.'],
        say:`ZIP ${r.zip} in ${r.city.label}. ${speakMeasure(r.city,r.zip,'engagement')} ${speakMeasure(r.city,r.zip,'poverty')}`};}},

    {name:'find_zips',title:'Rank ZIPs in a city by a measure',
      description:'Lists ZIPs in one city ranked by a measure, optionally keeping only ZIPs that pass up to three filters (e.g. poverty at least 20). ZIPs with limited data on any used measure are left out and counted.',
      inputSchema:{type:'object',properties:{
        city:{type:'string',description:'City id or label.'},
        measure:{type:'string',enum:MEASURE_KEYS},
        order:{type:'string',enum:['highest','lowest'],default:'highest'},
        limit:{type:'integer',minimum:1,maximum:20,default:5},
        filters:{type:'array',maxItems:3,items:{type:'object',properties:{measure:{type:'string',enum:MEASURE_KEYS},min:{type:'number'},max:{type:'number'}},required:['measure'],additionalProperties:false}}},
        required:['city','measure'],additionalProperties:false},annotations:READ,
      run:({city,measure,order='highest',limit=5,filters=[]})=>{
        const c=resolveCity(city),get=key=>{const m=ZIP_MEASURES.find(m=>m.key===key);if(!m)throw new ToolError(`Unknown measure "${key}".`,'Use a measure key from get_place_lab_guide.',MEASURE_KEYS);return m;};
        const m=get(measure),fs=filters.map(f=>({...f,m:get(f.measure)}));
        if(!['highest','lowest'].includes(order))throw new ToolError(`Unknown order "${order}".`,'Use "highest" or "lowest".',['highest','lowest']);
        const all=areasOf(c),usable=all.filter(a=>Number.isFinite(m.value(a))&&fs.every(f=>Number.isFinite(f.m.value(a))));
        const kept=usable.filter(a=>fs.every(f=>(f.min==null||f.m.value(a)>=f.min)&&(f.max==null||f.m.value(a)<=f.max)));
        kept.sort((a,b)=>order==='highest'?m.value(b)-m.value(a):m.value(a)-m.value(b));
        const top=kept.slice(0,Math.max(1,Math.min(20,Math.floor(limit))));
        return {city:c.label,measure:m.key,unit:m.unit,order,matched:kept.length,excluded_for_limited_data:all.length-usable.length,
          zips:top.map(a=>({zip:a.zip,value:round(m.value(a)),display:m.format(m.value(a)),...Object.fromEntries(fs.map(f=>[f.m.key,round(f.m.value(a))]))})),
          say:top.length?`In ${c.label}, the ${order} ${m.label.toLowerCase()}${fs.length?' among matching ZIPs':''} is in ZIP ${top[0].zip} at ${m.format(m.value(top[0]))}${top.length>1?`, then ${top.slice(1,3).map(a=>a.zip).join(' and ')}`:''}.`:`No ZIPs in ${c.label} match those filters.`};
      }},

    {name:'compare_past_projects',title:'What changed around past projects',
      description:'Returns the past-projects table: for each eligible project, the change near it (within 500 m) from two years before opening to two years after, minus the same change 1.5–8 km away. Includes the kind-level average, how many improved, the reliability of each measure, and whether project kind predicts outcomes (it did not). Descriptive only. Does not change the screen; use show_past_projects to show it.',
      inputSchema:{type:'object',properties:{kind:{type:'string',enum:KINDS,default:'all',description:'Kind of project, or "all".'}},additionalProperties:false},annotations:READ,
      run:({kind='all'})=>{
        if(!KINDS.includes(kind))throw new ToolError(`Unknown kind "${kind}".`,'Use a project kind from get_place_lab_guide.',KINDS);
        const s=familySummary(rows,kind);
        return {kind,projects:s.members.map(r=>({id:r.id,name:r.project,city:project(r.id).city_label,kind:FAMILIES[r.family].label,opened:r.opening,...changes(r)})),
          summary:Object.fromEntries(OUTCOMES.map(o=>[OUTCOME_KEYS[o.key],{average:round(s.outcomes[o.key].mean,3),min:round(s.outcomes[o.key].min,3),max:round(s.outcomes[o.key].max,3),improved:s.outcomes[o.key].better,of:s.n,unit:OUTCOME_UNITS[o.key]}])),
          reliability:reliability(),
          does_kind_predict:{answer:'No',detail:`Holding out each of ${kindCheck.activity.n} projects, the average for its kind missed its engagement change by ${Math.round(100*kindCheck.activity.family_mae)} log points, against ${Math.round(100*kindCheck.activity.overall_mae)} for the plain all-project average. Knowing the kind never helped on any measure.`},
          excluded:model.excluded_projects.map(p=>({id:p.id,name:p.project,reason:p.reason})),
          notes:['Lower is better for the two negative-mention measures.','Several post-opening windows include 2020.'],
          say:`For ${kindLabel(kind)}, ${s.n} projects: engagement beat the surroundings near ${s.outcomes.activity.better} and sentiment near ${s.outcomes.sentiment.better}. Knowing the kind of project did not predict how it went.`};
      }},

    {name:'get_project_history',title:'Detail for one past project',
      description:'Returns one past project\'s periods (early, pre-opening, post-opening) near the project and in its comparison area: reviews, average sentiment and negative-mention rates, plus comparison-adjusted changes and the topics whose discussion changed most.',
      inputSchema:{type:'object',properties:{project_id:{type:'string',description:'Project id from get_place_lab_guide, e.g. "the-rail-park".'}},required:['project_id'],additionalProperties:false},annotations:READ,
      run:({project_id})=>{
        const p=project(project_id),h=history.projects.find(h=>h.id===p.id),r=rows.find(r=>r.id===p.id);
        const period=x=>x?{years:Object.keys(x.by_year||{}).sort(),reviews:x.n_reviews,sentiment:round(x.mean_sentiment),negative_access_pct:round(100*x.access_friction_share,2),negative_public_space_pct:round(100*x.public_realm_complaint_share,2)}:null;
        const topics=insights.historicalTopics(h,'discussion').sort((a,b)=>Math.abs(b.value)-Math.abs(a.value)).slice(0,5).map(t=>({topic:t.topic,adjusted_change_pp:round(t.value,2),near_pre_pct:round(t.nearPre,1),near_post_pct:round(t.nearPost,1),sparse:t.sparse}));
        return {id:p.id,name:p.name,city:p.city_label,kind:r?FAMILIES[r.family].label:null,opened:h.opening,project_type:p.project_type,reported_cost_millions:p.cost_millions,
          near_within_500m:Object.fromEntries(['early','pre','post'].map(k=>[k,period(h.periods.near[k])])),
          comparison_1500_8000m:Object.fromEntries(['early','pre','post'].map(k=>[k,period(h.periods.far[k])])),
          adjusted_changes:r?changes(r):null,
          ...(r?{}:{note:model.excluded_projects.find(x=>x.id===p.id)?.reason??'Not included in comparisons.'}),
          top_topic_changes:topics,reliability:reliability(),
          say:r?`${p.name} in ${p.city_label} opened ${h.opening.slice(0,7)}. Compared with its surroundings, reviews changed ${fmtChange('activity',changeOf(r,'activity'))} and sentiment ${fmtChange('sentiment',changeOf(r,'sentiment'))}.`:`${p.name} is not in the comparison table: too few reviewed businesses nearby before opening.`};
      }},

    {name:'define_term',title:'Define a Place Lab term',
      description:'Looks up a term from the methodology glossary by key or name (e.g. "business engagement", "comparison area", "VADER") and returns its definition, calculation and caveat.',
      inputSchema:{type:'object',properties:{term:{type:'string',minLength:2}},required:['term'],additionalProperties:false},annotations:READ,
      run:({term})=>{
        const q=String(term).toLowerCase().trim(),entries=Object.entries(GLOSSARY);
        const hit=entries.find(([k,e])=>k===q.replace(/\s+/g,'_')||e.term.toLowerCase()===q)??entries.find(([k,e])=>e.term.toLowerCase().includes(q));
        if(!hit)throw new ToolError(`No glossary term matches "${term}".`,'Try a shorter name or one of the listed keys.',Object.keys(GLOSSARY));
        const [k,e]=hit;
        return {key:k,term:e.term,category:CATEGORIES[e.category],definition:e.definition,calculation:e.formula??null,caution:e.caution??null,link:`methods.html#term-${k}`,say:`${e.term}: ${e.definition}`};
      }},

    {name:'show_on_map',title:'Show a city, ZIP or map layer to the user',
      description:'Changes what the user sees: switches city, selects and zooms to a ZIP, and/or changes the heatmap focus, then scrolls to the map. Changes only the on-screen view. Returns what is now on screen.',
      inputSchema:{type:'object',properties:{city:{type:'string',description:'City id or label.'},zip:{type:'string',pattern:'^\\d{5}$'},focus:{type:'string',enum:FOCUS_KEYS}},minProperties:1,additionalProperties:false},annotations:VIEW,
      run:({city,zip,focus})=>{
        if(city==null&&zip==null&&focus==null)throw new ToolError('Nothing to show.','Pass a city, a zip, a focus, or a combination.');
        if(focus!=null&&!FOCUS_KEYS.includes(focus))throw new ToolError(`Unknown focus "${focus}".`,'Use a map focus key from get_place_lab_guide.',FOCUS_KEYS);
        const target=zip!=null?resolveZip(zip,city):{city:resolveCity(city)??resolveCity(view.current().city),zip:null};
        view.showOnMap({city:target.city.id,zip:target.zip,focus});
        if(view.current().section!=='map')view.goTo('map');
        return describe();
      }},

    {name:'set_map_time',title:'Choose the period the ZIP map describes',
      description:'Sets the period behind the ZIP map, the ZIP profile and get_zip_profile. mode "snapshot" shows one period and its change from the same period a year earlier; mode "compare" compares two equal periods. Write periods as "2016", "2016Q3" or "2016-07". grain is quarter or month; smooth (month grain only) averages the last 1, 3 or 12 months. start_at_project compares up to two years either side of a past project\'s opening and selects its ZIP. reset restores 2012–2014 against 2019–2021. Data run from January 2012 to December 2021. Changes only the on-screen view.',
      inputSchema:{type:'object',properties:{mode:{type:'string',enum:['snapshot','compare']},grain:{type:'string',enum:['quarter','month']},
        period:{type:'string',description:'Snapshot period, e.g. "2016Q3".'},from:{type:'string',description:'Start of the earlier compared period.'},to:{type:'string',description:'Start of the later compared period.'},
        length:{type:'integer',minimum:1,description:'Length of each compared period, in quarters or months.'},smooth:{type:'integer',enum:[1,3,12]},
        start_at_project:{type:'string',description:'Past project id from get_place_lab_guide.'},reset:{type:'boolean'}},minProperties:1,additionalProperties:false},annotations:VIEW,
      run:({mode,grain,period,from,to,length,smooth,start_at_project,reset})=>{
        const now=view.time?.();
        if(!now)throw new ToolError('The map timeline did not load.','Reload the page; the map still shows 2012–2014 against 2019–2021.');
        if(mode!=null&&!['snapshot','compare'].includes(mode))throw new ToolError(`Unknown mode "${mode}".`,'Use snapshot or compare.',['snapshot','compare']);
        if(grain!=null&&!['quarter','month'].includes(grain))throw new ToolError(`Unknown grain "${grain}".`,'Use quarter or month.',['quarter','month']);
        let result;
        if(reset)result=view.setTime({...DEFAULT_TIME});
        else if(start_at_project!=null){project(start_at_project);result=view.startAtProject(start_at_project);}
        else{
          const g=grain??now.setting.grain,patch={};
          const at=(text,name)=>{const i=view.parsePeriod(g,text);if(i==null)throw new ToolError(`"${text}" is not a period in the data.`,`Use a ${name} between ${now.first} and ${now.last}, written like 2016, 2016Q3 or 2016-07.`);return i;};
          if(grain!=null)patch.grain=grain;if(mode!=null)patch.mode=mode;if(smooth!=null)patch.smooth=smooth;if(length!=null)patch.length=length;
          if(period!=null){patch.at=at(period,'period');patch.mode??='snapshot';}
          if(from!=null){patch.from=at(from,'start');patch.mode??='compare';}
          if(to!=null){patch.to=at(to,'start');patch.mode??='compare';}
          result=view.setTime(patch);
        }
        const {setting,labels}=result;
        const limits=labels.minimum?` Each period needs ${labels.minimum} reviews, or the ZIP shows limited data.`:'';
        return {map_time:result,say:setting.mode==='compare'?`The map now compares ${labels.change}.${limits}`:`The map now shows ${labels.level}, with change from ${labels.base}.${limits}`};
      }},

    {name:'show_past_projects',title:'Show past projects to the user',
      description:'Scrolls to the past-projects table or charts and changes them: filter to a kind of project, open one project in the charts, and/or pick a chart (engagement, sentiment, access, realm, topics). Changes only the on-screen view. Returns what is now on screen.',
      inputSchema:{type:'object',properties:{kind:{type:'string',enum:KINDS},project_id:{type:'string'},chart:{type:'string',enum:CHART_KEYS}},minProperties:1,additionalProperties:false},annotations:VIEW,
      run:({kind,project_id,chart})=>{
        if(kind!=null&&!KINDS.includes(kind))throw new ToolError(`Unknown kind "${kind}".`,'Use a project kind from get_place_lab_guide.',KINDS);
        if(chart!=null&&!CHART_KEYS.includes(chart))throw new ToolError(`Unknown chart "${chart}".`,'Use one of the listed charts.',CHART_KEYS);
        let k=kind;
        if(project_id!=null){
          project(project_id);
          const own=kindOf(project_id);
          if(!own)throw new ToolError(`${project(project_id).name} is not in the comparison table.`,'It had too few reviewed businesses nearby before opening. Use get_project_history for its data.');
          // Keep the current filter when it already contains the project; otherwise switch to its kind.
          const current=view.current().past_projects?.kind??'all';
          if(k==null)k=current==='all'||current===own?undefined:own;
          else if(k!=='all'&&k!==own)throw new ToolError(`${project(project_id).name} is a ${FAMILIES[own].label} project, not ${FAMILIES[k].label}.`,'Omit kind, or pass its kind or "all".');
        }
        view.showPastProjects({kind:k,project_id,chart});
        return describe();
      }}
  ];

  return tools.map(({run,...definition})=>({...definition,execute:async(args={})=>{
    try{
      if(!args||typeof args!=='object'||Array.isArray(args))throw new ToolError('Arguments must be a JSON object.','Pass {} when a tool takes no arguments.');
      const allowed=Object.keys(definition.inputSchema.properties);
      const extra=Object.keys(args).filter(k=>!allowed.includes(k));
      if(extra.length)throw new ToolError(`Unexpected argument${extra.length>1?'s':''}: ${extra.join(', ')}.`,allowed.length?`This tool accepts: ${allowed.join(', ')}.`:'This tool takes no arguments; pass {}.');
      const missing=(definition.inputSchema.required??[]).filter(k=>args[k]==null);
      if(missing.length)throw new ToolError(`Missing required argument: ${missing.join(', ')}.`,`Required: ${definition.inputSchema.required.join(', ')}.`);
      return JSON.parse(JSON.stringify({ok:true,...run(args)}));
    }catch(error){
      return {ok:false,error:error.message,...(error.hint?{hint:error.hint}:{}),...(error.valid_values?{valid_values:error.valid_values}:{}),say:`${error.message} ${error.hint??''}`.trim()};
    }
  }}));
}

// WebMCP: Chrome serialises whatever execute returns, so return the plain result object;
// wrapping it in MCP text content would hand agents doubly escaped JSON.
// Chrome passes inputs as an object plus a cancellation signal; only the inputs are used.
export async function registerPlaceTools(context,tools){
  if(!context)return false;
  const wrapped=tools.map(t=>({...t,execute:args=>t.execute(args??{})}));
  if(typeof context.provideContext==='function'){await context.provideContext({tools:wrapped});return true;}
  if(typeof context.registerTool!=='function')return false;
  for(const tool of wrapped)await context.registerTool(tool);
  return true;
}
