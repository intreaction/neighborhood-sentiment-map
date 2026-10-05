import {PERIODS,COMBINED_VIEWS,combinedMeasures,combinedEvidence,COMBINED_CATEGORIES,FOCUSES,areaValue,areaTextColor,formatAreaValue,areaAt} from './place_area_math.mjs';
const n=value=>Number.isFinite(value)?Math.round(value).toLocaleString('en-US'):'—';
// Computes the heatmap legend and area evidence for the selected ZIP and writes them to the panel store.
export function createAreaExplorer({areaData,mapData,store,getState,getScene,onChange=()=>{},onSelect=()=>{}}) {
  function combinedLegend(f){
    const [a,b]=combinedMeasures(f);
    if(!a)return null;
    return {columnTitle:FOCUSES[b.focus].title,columns:[[b.low,b.lowRule],[b.high,b.highRule]],note:[a,b].map(m=>m.note).join(' '),
      rows:[[a.low,a.lowRule],[a.high,a.highRule]].map((label,r)=>({label,cells:[0,1].map(c=>{const i=r*2+c;return {color:COMBINED_CATEGORIES[i].color,text:i===3?'#fff':'#172f2c',label:['Neither',b.short,a.short,'Both'][i],aria:formatAreaValue(i,f)};})}))};
  }
  let selected=null,lastCity=null,lastPoint=null;
  const focus=()=>{const v=store.get();return v.focus==='income'?v.economic:v.focus;};
  function update() {
    const state=getState(),city=areaData.cities.find(c=>c.id===state.city),geometry=mapData.cities.find(c=>c.id===state.city);
    const currentPoint=`${state.city}:${state.longitude}:${state.latitude}`;
    const patch={};
    if(lastCity!==state.city){patch.zips=city.areas.map(a=>a.zip).sort();lastCity=state.city;}
    if(lastPoint!==currentPoint){selected=areaAt([state.longitude,state.latitude],geometry.features);lastPoint=currentPoint;}
    const f=focus(),spec=FOCUSES[f],row=city.areas.find(a=>a.zip===selected);
    const isCombined=!!COMBINED_VIEWS[f],includesMeasure=m=>f===m||COMBINED_VIEWS[f]?.measures.includes(m);
    const lines=row?[
      `${n(row.early.reviews)} reviews in ${PERIODS.base} → ${n(row.late.reviews)} in ${PERIODS.level}.`,
      ...(f==='income'||includesMeasure('poverty')?[row.acs_year?`ACS ${row.acs_year-4}–${row.acs_year}: household income ${formatAreaValue(row.median_income,'income')}${row.income_moe!==null?', ±$'+n(row.income_moe)+' margin of error':''}; poverty ${formatAreaValue(row.poverty_pct,'poverty')}.`:'The ACS has no estimate for this ZIP.']:[]),
      ...(f==='activity'?[`${n(row.business_inventory)} Yelp listings in the January 2022 inventory. ${row.area_km2.toFixed(1)} km² of mapped area.`]:[]),
      ...(includesMeasure('experience')?[`Absolute sentiment change: ${formatAreaValue(row.sentiment_change,'experience')}. The map compares this change with the rest of the city.`]:[]),
      ...(includesMeasure('access')?[`${n(row.access_mentions)} access/parking mentions in ${PERIODS.level}. Mentions can be positive or negative.`]:[]),
      ...(includesMeasure('decline')?[`Business engagement change: ${formatAreaValue(row.growth_pct,'decline')}.`]:[]),
      ...(includesMeasure('decline')?[`Compares ${PERIODS.change}. A change in reviews does not mean businesses opened or closed.`]:[])
    ]:['Hover over the map or choose a ZIP to see its numbers.'];
    store.set({...patch,zip:selected,heatPeriod:spec.period,
      legend:{hidden:f==='none',title:spec.title+(spec.unit?' · '+spec.unit:''),low:spec.ends[0],high:spec.ends[1],diverging:spec.palette==='diverging',combined:isCombined?combinedLegend(f):null},
      heatExplanation:spec.note,
      heatCoverage:f==='none'?null:`${city.areas.filter(a=>areaValue(a,f)!==null).length} of ${city.areas.length} mapped areas have data for this focus. Hatched = limited or missing data.`,
      area:{heading:selected?'ZIP '+selected:'Explore an area',combined:isCombined,metricColor:areaTextColor(areaValue(row,f),f),
        metric:row&&f!=='none'?formatAreaValue(areaValue(row,f),f):'—',
        metricLabel:f==='none'?'Choose a heatmap focus':spec.title+(f==='activity'?' · reviews / km² / year':''),evidence:lines}});
    getScene()?.setHeatmap(f,city.areas,selected);
    onChange(f);
  }
  function selectArea(zip){selected=zip||null;if(selected){onSelect(selected);getScene()?.focusArea(selected);}else update();}
  function focusArea(){if(selected)getScene()?.focusArea(selected);}
  return {update,selectArea,focusArea,inspectPoint(point){const city=mapData.cities.find(c=>c.id===getState().city);selected=areaAt([point.longitude,point.latitude],city.features);update();},snapshot(){const row=areaData.cities.find(c=>c.id===getState().city).areas.find(a=>a.zip===selected);return {...(COMBINED_VIEWS[focus()]?{measures:combinedEvidence(row,focus()),category:formatAreaValue(areaValue(row,focus()),focus())}:{}),focus:focus(),zip:selected,source_version:areaData.version,period:FOCUSES[focus()].period};}};
}
