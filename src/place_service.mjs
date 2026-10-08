// Model-independent query and command planning. No browser or LLM dependency.
import {readFileSync} from 'node:fs';
import {createHash} from 'node:crypto';
import {createPlaceTools} from './place_tools.mjs';
import {ZIP_MEASURES} from './place_measures.mjs';
import {areaAnchor} from './place_area_math.mjs';
import {DEFAULT_TIME,applyTime,clampTimeSetting,parsePeriod,periodCount,periodLabel,zipSeries} from './place_timeline.mjs';

export class BridgeError extends Error {
  constructor(message,code='invalid_arguments',status=400){super(message);this.code=code;this.status=status;}
}
// Validate the schema vocabulary used by the public tools, including nested inputs.
export function validate(schema,value,path='arguments'){
  if(schema.type==='object'){
    if(!value||typeof value!=='object'||Array.isArray(value))throw new BridgeError(`${path} must be an object.`);
    for(const key of schema.required??[])if(value[key]===undefined)throw new BridgeError(`${path}.${key} is required.`);
    if(schema.minProperties&&Object.keys(value).length<schema.minProperties)throw new BridgeError(`${path} needs at least one property.`);
    for(const [key,v] of Object.entries(value)){
      if(!schema.properties?.[key]){if(schema.additionalProperties===false)throw new BridgeError(`Unknown ${path}.${key}.`);continue;}
      validate(schema.properties[key],v,`${path}.${key}`);
    }
  }else if(schema.type==='array'){
    if(!Array.isArray(value))throw new BridgeError(`${path} must be an array.`);
    if(schema.maxItems&&value.length>schema.maxItems)throw new BridgeError(`${path} allows at most ${schema.maxItems} items.`);
    if(schema.minItems&&value.length<schema.minItems)throw new BridgeError(`${path} needs at least ${schema.minItems} items.`);
    value.forEach((v,i)=>validate(schema.items,v,`${path}[${i}]`));
  }else{
    const type=schema.type;
    if(type==='integer'?!Number.isInteger(value):type==='number'?typeof value!=='number'||!Number.isFinite(value):typeof value!==type)throw new BridgeError(`${path} must be ${type}.`);
    if(schema.enum&&!schema.enum.includes(value))throw new BridgeError(`${path} must be one of: ${schema.enum.join(', ')}.`);
    if(schema.minimum!==undefined&&value<schema.minimum||schema.maximum!==undefined&&value>schema.maximum)throw new BridgeError(`${path} is outside its allowed range.`);
    if(schema.pattern&&!new RegExp(schema.pattern).test(value))throw new BridgeError(`${path} has an invalid format.`);
    if(schema.minLength&&value.length<schema.minLength)throw new BridgeError(`${path} is too short.`);
  }
}
const object=(properties,required=[])=>({type:'object',properties,required,additionalProperties:false});
const str={type:'string'},zip={type:'string',pattern:'^\\d{5}$'},bool={type:'boolean'};

export function createPlaceService(root){
  const assets=new Map();
  const load=name=>{const raw=readFileSync(new URL(`../web/${name}.json`,root));assets.set(`${name}.json`,raw);return JSON.parse(raw);};
  const data=load('place-data'),published=load('place-areas'),timeline=load('place-timeline'),history=load('place-history'),model=load('place-model'),map=load('place-map'),findings=load('findings-data'),manifest=load('place-build-manifest');
  const hash=createHash('sha256');for(const [name,raw] of assets)hash.update(name).update(raw);
  const revision=hash.digest('hex');
  function context(snapshot={}){
    const state={section:'map',city:'Philadelphia',zip:null,focus:'activity',measure:null,past_projects:{kind:'all',project_id:null,chart:'engagement'},...structuredClone(snapshot)};
    const areas=structuredClone(published);
    let setting=clampTimeSetting(timeline,{...DEFAULT_TIME,...snapshot.time?.setting});
    const update=()=>{applyTime(areas,timeline,setting);state.map_period=areas.time.labels;};update();
    const view={
      current:()=>structuredClone(state),
      showOnMap:({city,zip,focus})=>{if(city&&city!==state.city){state.city=city;state.zip=null;}if(zip)state.zip=zip;if(focus)state.focus=focus;},
      showPastProjects:args=>{Object.assign(state.past_projects,Object.fromEntries(Object.entries(args).filter(([,v])=>v!=null)));state.section=args.chart?'project_charts':'past_projects';},
      goTo:section=>{state.section=section;},highlightMeasure:measure=>{state.measure=measure;},zoom:()=>{},
      anchors:city=>Object.fromEntries(map.cities.find(c=>c.id===city).features.map(f=>[f.properties.zip,areaAnchor(f)])),
      time:()=>({setting:{...setting},labels:{...areas.time.labels},periods:periodCount(timeline,setting.grain),first:periodLabel(timeline,setting.grain,0),last:periodLabel(timeline,setting.grain,periodCount(timeline,setting.grain)-1)}),
      parsePeriod:(grain,text)=>parsePeriod(timeline,grain,text),
      setTime:patch=>{
        if(patch.grain&&patch.grain!==setting.grain){
          setting=patch.grain==='month'?{...setting,grain:'month',at:setting.at*3+2,from:setting.from*3,to:setting.to*3,length:setting.length*3,smooth:3}:{...setting,grain:'quarter',at:Math.floor(setting.at/3),from:Math.floor(setting.from/3),to:Math.floor(setting.to/3),length:Math.max(1,Math.round(setting.length/3))};
        }
        setting=clampTimeSetting(timeline,{...setting,...patch});update();return view.time();
      },
      startAtProject:id=>{
        const p=history.projects.find(p=>p.id===id),location=data.projects.find(p=>p.id===id),u=setting.grain==='quarter'?3:1,n=periodCount(timeline,setting.grain);
        const open=parsePeriod(timeline,setting.grain,p.opening.slice(0,7)),length=Math.max(1,Math.min(24/u,open,n-1-open));
        if(location.city_id)state.city=location.city_id;
        return view.setTime({mode:'compare',length,from:open-length,to:open+1});
      }
    };
    const tools=createPlaceTools({data,areas,history,model,validation:findings.text_validation,view});
    const call=async(name,args={})=>{const t=tools.find(t=>t.name===name);if(!t)throw new BridgeError(`Unknown tool ${name}.`);validate(t.inputSchema,args);const result=await t.execute(args);if(!result.ok)throw new BridgeError(result.error);return result;};
    return {areas,view,call,tools};
  }
  const original=context().tools;
  const schema=name=>structuredClone(original.find(t=>t.name===name).inputSchema);
  const timeSchema=schema('set_map_time');
  const queryProperties={city:str,time:timeSchema};
  const rank=schema('find_zips');rank.required=['measure'];Object.assign(rank.properties,{time:timeSchema,show:bool});
  const profile=schema('get_zip_profile');Object.assign(profile.properties,{time:timeSchema,show:bool});
  const viewProperties={...schema('show_on_map').properties,...schema('show_past_projects').properties,section:schema('go_to').properties.section};
  const definitions=[
    ['get_context','Get available measures, coverage, connected page state and current period.',object({})],
    ['rank_areas','Rank ZIPs by a measure in the specified or selected city. Activity means engagement density; reviews means total count. Optional show selects the first result in one call.',rank],
    ['get_area_profile','Get a ZIP profile with units, periods, city medians, ranks and limited-data indicators. Optional show selects it.',profile],
    ['compare_areas','Compare two to five ZIPs using the same period. Each ZIP is compared with its own city.',object({zips:{type:'array',minItems:2,maxItems:5,items:zip},time:timeSchema},['zips'])],
    ['get_area_timeline','Return a ZIP activity and sentiment timeline. Grain is quarter or month; smoothing applies to months.',object({...queryProperties,zip,grain:{type:'string',enum:['quarter','month']},smooth:{type:'integer',enum:[1,3,12]}},['zip'])],
    ['compare_projects','Compare historical project outcomes by kind, including reliability and exclusions.',schema('compare_past_projects')],
    ['get_project','Get one past project history, comparison-adjusted changes, topics and reliability.',schema('get_project_history')],
    ['define_term','Look up a measure definition, calculation and interpretation.',schema('define_term')],
    ['set_view','Change city, ZIP, map layer, section, project filter or chart. Requires a connected browser.',{...object(viewProperties),minProperties:1}],
    ['set_time','Change the connected page timeline. Query tools also accept a time override without changing the page.',timeSchema],
    ['navigate','Move between sections, zoom in/out or select a neighboring ZIP. Requires a connected browser.',object({direction:{type:'string',enum:['up','down','left','right','in','out','north','south','east','west']},steps:{type:'integer',minimum:1,maximum:5}},['direction'])]
  ].map(([name,description,inputSchema])=>({name,description,inputSchema,annotations:{readOnlyHint:!['rank_areas','get_area_profile','set_view','set_time','navigate'].includes(name),destructiveHint:false,openWorldHint:false}}));
  async function plan(name,args,snapshot=null){
    const definition=definitions.find(t=>t.name===name);if(!definition)throw new BridgeError(`Unknown tool ${name}. Available: ${definitions.map(t=>t.name).join(', ')}.`);
    validate(definition.inputSchema,args);
    const c=context(snapshot??{}),actions=[];
    if(args.time)await c.call('set_map_time',args.time);
    const requireCity=()=>{const city=args.city??snapshot?.city;if(!city)throw new BridgeError('Specify city, or connect one presentation page.','context_required');return city;};
    const action=async(tool,arguments_)=>{await c.call(tool,arguments_);actions.push({tool,arguments:arguments_});};
    const show=async(zip_,city,focus)=>{
      if(args.time)actions.push({tool:'set_map_time',arguments:args.time});
      await action('show_on_map',{city,zip:zip_,...(focus?{focus}:{})});
    };
    let result;
    if(name==='get_context')result={...await c.call('get_place_lab_guide'),current_view:snapshot,tools:definitions,coverage:manifest.summary};
    else if(name==='rank_areas'){
      const {time,show:display,...rankArgs}=args;result=await c.call('find_zips',{...rankArgs,city:requireCity()});
      result.period={...c.view.time().labels};result.minimum_reviews=c.view.time().labels.minimum;
      result.interpretation=ZIP_MEASURES.find(m=>m.key===args.measure).label;
      if(display&&result.zips.length)await show(result.zips[0].zip,result.city,ZIP_MEASURES.find(m=>m.key===args.measure).focus??'none');
    }else if(name==='get_area_profile'){
      result=await c.call('get_zip_profile',{zip:args.zip,...(args.city?{city:args.city}:{})});
      if(args.show)await show(args.zip,result.city);
    }else if(name==='compare_areas')result={ok:true,areas:await Promise.all(args.zips.map(zip=>c.call('get_zip_profile',{zip}))),say:`Compared ZIPs ${args.zips.join(', ')} using the same historical period.`};
    else if(name==='get_area_timeline'){
      const profile=await c.call('get_zip_profile',{zip:args.zip,...(args.city?{city:args.city}:{})});
      const city=data.cities.find(c=>c.label===profile.city).id,setting={...c.view.time().setting,grain:args.grain??c.view.time().setting.grain,smooth:args.smooth??c.view.time().setting.smooth};
      result={ok:true,city:profile.city,zip:args.zip,grain:setting.grain,smooth:setting.smooth,series:zipSeries(timeline,city,args.zip,setting),units:{reviews:'reviews per period',sentiment:'VADER compound',metro_sentiment:'VADER compound in the rest of the metro'},say:`Historical ${setting.grain} timeline for ZIP ${args.zip} in ${profile.city}, 2012 through 2021.`};
    }else if(name==='compare_projects')result=await c.call('compare_past_projects',args);
    else if(name==='get_project')result=await c.call('get_project_history',args);
    else if(name==='define_term')result=await c.call('define_term',args);
    else if(name==='set_time'){await action('set_map_time',args);result={ok:true,say:'Timeline command prepared.'};}
    else if(name==='navigate'){
      if(['north','south','east','west'].includes(args.direction)){for(let i=0;i<(args.steps??1);i++)await action('move_to_neighbor',{direction:args.direction});}
      else await action('navigate',args);
      result={ok:true,say:'Navigation command prepared.'};
    }else if(name==='set_view'){
      const {city,zip,focus,section,kind,project_id,chart}=args;
      const clean=obj=>Object.fromEntries(Object.entries(obj).filter(([,v])=>v!==undefined));
      if(city!==undefined||zip!==undefined||focus!==undefined)await action('show_on_map',clean({city,zip,focus}));
      if(kind!==undefined||project_id!==undefined||chart!==undefined)await action('show_past_projects',clean({kind,project_id,chart}));
      if(section!==undefined)await action('go_to',{section});
      result={ok:true,say:'View command prepared.'};
    }
    return {result,actions,context:{city:result.city??c.view.current().city,time:c.view.time(),dataset_revision:revision},queryOnly:!['set_view','set_time','navigate'].includes(name)};
  }
  return {assets,revision,definitions,plan};
}
