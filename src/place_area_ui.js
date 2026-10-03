import {COMBINED_POVERTY_THRESHOLD,COMBINED_CATEGORIES,FOCUSES,areaValue,areaTextColor,formatAreaValue,areaAt} from './place_area_math.mjs';
const $=id=>document.getElementById(id);
const n=value=>Number.isFinite(value)?Math.round(value).toLocaleString('en-US'):'—';
export function createAreaExplorer({areaData,mapData,getState,getScene,onChange=()=>{},onSelect=()=>{}}) {
  const legend=$('combinedLegend');
  const table=document.createElement('table');
  table.innerHTML=`<caption>Review activity change →</caption><thead><tr><td></td><th scope="col">Stable / growing<br>≥ 0%</th><th scope="col">Declining<br>&lt; 0%</th></tr></thead><tbody><tr><th scope="row">Lower poverty<br>&lt; ${COMBINED_POVERTY_THRESHOLD}%</th><td></td><td></td></tr><tr><th scope="row">Higher poverty<br>≥ ${COMBINED_POVERTY_THRESHOLD}%</th><td></td><td></td></tr></tbody>`;
  table.querySelectorAll('tbody td').forEach((cell,i)=>{cell.style.backgroundColor=COMBINED_CATEGORIES[i].color;cell.setAttribute('aria-label',COMBINED_CATEGORIES[i].label);cell.textContent=['Neither','Decline','Poverty','Both'][i];cell.style.color=i===3?'#fff':'#172f2c';});
  legend.append(table);
  const thresholdNote=document.createElement("p");thresholdNote.textContent="20% poverty cutoff: exploratory, not a need designation.";legend.append(thresholdNote);
  let selected=null,lastCity=null,lastPoint=null;
  const focus=()=>$('focusSelect').value==='income'?$('economicMeasure').value:$('focusSelect').value;
  function update() {
    const state=getState(),city=areaData.cities.find(c=>c.id===state.city),geometry=mapData.cities.find(c=>c.id===state.city);
    const currentPoint=`${state.city}:${state.longitude}:${state.latitude}`;
    if(lastCity!==state.city){
      $('areaSelect').replaceChildren(new Option('Choose an area',''));
      for(const row of city.areas.slice().sort((a,b)=>a.zip.localeCompare(b.zip)))$('areaSelect').add(new Option('ZIP '+row.zip,row.zip));
      lastCity=state.city;
    }
    if(lastPoint!==currentPoint){selected=areaAt([state.longitude,state.latitude],geometry.features);lastPoint=currentPoint;}
    const f=focus(),spec=FOCUSES[f],row=city.areas.find(a=>a.zip===selected);
    $('economicControl').hidden=$('focusSelect').value!=='income';
    $('areaSelect').value=selected||'';
    $('heatLegend').hidden=f==='none';
    $('heatLegendTitle').textContent=spec.title+(spec.unit?' · '+spec.unit:'');
    $('heatPeriod').textContent=spec.period;
    $('heatLegendLow').textContent=spec.ends[0];$('heatLegendHigh').textContent=spec.ends[1];
    $('heatScale').hidden=f==='combined';
    legend.hidden=f!=='combined';
    $('areaMetric').classList.toggle('combined-signal',f==='combined');
    $('heatRamp').classList.toggle('diverging',spec.palette==='diverging');
    $('heatExplanation').textContent=spec.note;
    $('heatCoverage').textContent=`${city.areas.filter(a=>areaValue(a,f)!==null).length} of ${city.areas.length} mapped areas have data for this focus. Hatched = limited or missing data.`;
    $('heatCoverage').hidden=f==='none';
    $('areaHeading').textContent=selected?'ZIP '+selected:'Explore an area';
    $('areaMetric').style.color=areaTextColor(areaValue(row,f),f);
    $('areaMetric').textContent=row&&f!=='none'?formatAreaValue(areaValue(row,f),f):'—';
    $('areaMetricLabel').textContent=f==='none'?'Choose a heatmap focus':spec.title+(f==='activity'?' · reviews / km² / year':'');
    $('areaEvidence').replaceChildren();
    const lines=row?[
      `${n(row.early.reviews)} reviews in 2012–2014 → ${n(row.late.reviews)} in 2019–2021.`,
      ...(f==='income'||f==='poverty'||f==='combined'?[row.acs_year?`ACS ${row.acs_year-4}–${row.acs_year}: household income ${formatAreaValue(row.median_income,'income')}${row.income_moe!==null?' (±$'+n(row.income_moe)+' margin of error)':''}; poverty ${formatAreaValue(row.poverty_pct,'poverty')}.`:'No baseline ACS estimate available.']:[]),
      ...(f==='activity'?[`${n(row.business_inventory)} Yelp listings in the January 2022 inventory. ${row.area_km2.toFixed(1)} km² of mapped area.`]:[]),
      ...(f==='experience'?[`Absolute sentiment change: ${formatAreaValue(row.sentiment_change,'experience')}. The heatmap compares this change with the rest of the city.`]:[]),
      ...(f==='access'?[`${n(row.access_mentions)} access/parking mentions out of ${n(row.late.reviews)} reviews. Mentions can be positive or negative.`]:[]),
      ...(f==='combined'?[`Review activity change: ${formatAreaValue(row.growth_pct,'decline')}.`]:[]),
      ...(f==='decline'||f==='combined'?[`Equal three-year windows; review activity, not verified business openings or closures.`]:[])
    ]:['Hover over the map or choose a ZIP to inspect the existing area analysis.'];
    for(const line of lines){const p=document.createElement('p');p.textContent=line;$('areaEvidence').append(p);}
    getScene()?.setHeatmap(f,city.areas,selected);
    onChange(f);
  }
  $('focusSelect').addEventListener('change',update);
  $('economicMeasure').addEventListener('change',update);
  $('areaSelect').addEventListener('change',()=>{selected=$('areaSelect').value||null;if(selected){onSelect(selected);getScene()?.focusArea(selected);}else update();});
  $('areaFocusButton').addEventListener('click',()=>{if(selected)getScene()?.focusArea(selected);});
  return {update,inspectPoint(point){const city=mapData.cities.find(c=>c.id===getState().city);selected=areaAt([point.longitude,point.latitude],city.features);update();},snapshot(){const row=areaData.cities.find(c=>c.id===getState().city).areas.find(a=>a.zip===selected);return {...(focus()==='combined'?{poverty_threshold_pct:COMBINED_POVERTY_THRESHOLD,decline_threshold_pct:0,poverty_pct:row?.poverty_pct??null,growth_pct:row?.growth_pct??null,category:formatAreaValue(areaValue(row,'combined'),'combined')}:{}),focus:focus(),zip:selected,source_version:areaData.version,period:FOCUSES[focus()].period};}};
}
