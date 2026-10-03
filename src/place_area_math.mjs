// Area colors describe the existing ZIP analysis, never inferred block-level values.
// Category IDs are color lookups, not an ordered need score.
export const COMBINED_CATEGORIES=[
  {label:'Lower poverty · stable / growing',color:'#e3e5e6'},
  {label:'Lower poverty · declining',color:'#d98b39'},
  {label:'Higher poverty · stable / growing',color:'#5992b5'},
  {label:'Higher poverty · declining',color:'#75578a'}
];
export const FOCUSES={
  activity:{label:'Reach active business areas',field:'annual_review_density',title:'Review activity',unit:'reviews / km² / year',period:'2019–2021 · annual average',note:'Recorded Yelp activity per square kilometre, including water inside the boundary. It does not measure visits or revenue.',range:[0,3000],log:true,ends:['0','3,000+'],palette:'sequential'},
  income:{label:'Support lower-income areas',field:'median_income',title:'Median household income',unit:'historical dollars',period:'Baseline ACS · 2007–2011 / 2008–2012',note:'Warmer areas have lower baseline household income. These are historical ZIP/ZCTA estimates, not reviewer incomes or current conditions.',range:[20000,100000],reverse:true,ends:['$100k+','$20k or less'],palette:'sequential'},
  poverty:{label:'Support lower-income areas',field:'poverty_pct',title:'Population below poverty',unit:'% of poverty-status population',period:'Baseline ACS · 2007–2011 / 2008–2012',note:'Warmer areas have a higher baseline poverty rate. The estimates describe the area, not individual Yelp reviewers.',range:[0,50],ends:['0%','50%+'],palette:'sequential'},
  decline:{label:'Explore declining activity',field:'growth_pct',title:'Change in review activity',unit:'% change in review count',period:'2012–2014 → 2019–2021',note:'Warm = decline; teal = growth. Both three-year periods need 100 reviews. The later period includes COVID-19. First or absent reviews do not establish business openings or closures.',range:[-100,100],reverse:true,ends:['Growth +100% or more','Decline −100%'],palette:'diverging'},
  experience:{label:'Explore worsening experiences',field:'relative_sentiment_change',title:'Sentiment change vs. the city',unit:'VADER score difference',period:'2012–2014 → 2019–2021',note:'Warm = sentiment changed less favorably than the rest of the study metro. This is whole-review business sentiment. Relative improvement can occur even when absolute sentiment falls.',range:[-.15,.15],reverse:true,ends:['Better +0.15 or more','Worse −0.15 or less'],palette:'diverging'},
  access:{label:'Investigate access concerns',field:'access_share_pct',title:'Access & parking discussion',unit:'% of reviews mentioning access',period:'2019–2021 · existing keyword analysis',note:'Parking, walking, transit and accessibility mentions include praise and complaints. This is discussion frequency, not a validated complaint rate. At least 100 reviews required.',range:[0,15],ends:['0%','15%+'],palette:'sequential'},
  none:{label:'No heatmap',title:'Street map',note:'Choose a focus to explore existing area evidence.',period:'',range:[0,1],ends:['',''],palette:'sequential'}
};
// Shared measure definitions keep legends, cards, exports and classification aligned.
export const COMBINED_MEASURES={
  poverty:{focus:'poverty',field:'poverty_pct',threshold:20,operator:'>=',low:'Lower poverty',high:'Higher poverty',short:'Poverty',lowRule:'< 20%',highRule:'≥ 20%',note:'20% poverty cutoff: exploratory, not a need designation.'},
  decline:{focus:'decline',field:'growth_pct',threshold:0,operator:'<',low:'Stable / growing',high:'Declining',short:'Decline',lowRule:'≥ 0%',highRule:'< 0%',note:'Activity means review counts, not business closures. The later period includes COVID-19.'},
  experience:{focus:'experience',field:'relative_sentiment_change',threshold:0,operator:'<',low:'At / above city',high:'Below city',short:'Sentiment',lowRule:'≥ 0 VADER',highRule:'< 0 VADER',note:'Sentiment change is relative to the rest of the city, not necessarily an absolute decline.'},
  access:{focus:'access',field:'access_share_pct',threshold:5,operator:'>=',low:'Less discussion',high:'More discussion',short:'Access',lowRule:'< 5%',highRule:'≥ 5%',note:'5% mention cutoff: exploratory. Access discussion includes praise and complaints.'}
};
export const COMBINED_VIEWS={
  combined:{title:'Poverty + activity change',measures:['poverty','decline']},
  poverty_experience:{title:'Poverty + sentiment change',measures:['poverty','experience']},
  poverty_access:{title:'Poverty + access discussion',measures:['poverty','access']},
  decline_experience:{title:'Activity + sentiment change',measures:['decline','experience']}
};
for(const [key,view] of Object.entries(COMBINED_VIEWS)){
  const measures=view.measures.map(key=>COMBINED_MEASURES[key]);
  FOCUSES[key]={label:view.title,title:view.title,period:[...new Set(measures.map(m=>FOCUSES[m.focus].period))].join('; '),note:measures.map(m=>m.note).join(' ')+' Both measures must have data. Overlap is not a need score or a causal finding.',ends:['',''],palette:'categorical'};
}
export function combinedMeasures(focus){return COMBINED_VIEWS[focus]?.measures.map(key=>COMBINED_MEASURES[key])??[];}
export function combinedEvidence(area,focus){return combinedMeasures(focus).map(m=>({
  label:FOCUSES[m.focus].title,value:formatAreaValue(area?.[m.field],m.focus),
  period:m.focus==='poverty'?(area?.acs_year?`ACS ${area.acs_year-4}–${area.acs_year}`:'Baseline ACS unavailable'):FOCUSES[m.focus].period,
  field:m.field,raw_value:area?.[m.field]??null,threshold:m.threshold,operator:m.operator
}));}
export function areaValue(area,focus){
  if(COMBINED_VIEWS[focus]){
    const measures=combinedMeasures(focus);
    if(measures.some(m=>!Number.isFinite(area?.[m.field])))return null;
    return measures.reduce((category,m,i)=>category+((m.operator==='>='?area[m.field]>=m.threshold:area[m.field]<m.threshold)?(i===0?2:1):0),0);
  }
  const value=area?.[FOCUSES[focus]?.field];return Number.isFinite(value)?value:null;}
export function formatAreaValue(value,focus){
  if(!Number.isFinite(value))return 'Limited data';
  if(COMBINED_VIEWS[focus]){const [a,b]=combinedMeasures(focus);return `${value>=2?a.high:a.low} · ${value%2?b.high:b.low}`;}
  if(focus==='income')return '$'+Math.round(value).toLocaleString('en-US');
  if(['poverty','access','decline'].includes(focus))return `${focus==='decline'&&value>0?'+':''}${value.toFixed(1)}%`;
  if(focus==='experience')return `${value>0?'+':''}${value.toFixed(3)}`;
  return Math.round(value).toLocaleString('en-US');
}
export function areaColor(value,focus){
  if(!Number.isFinite(value))return '#929d9b';
  if(COMBINED_VIEWS[focus])return COMBINED_CATEGORIES[value]?.color??'#929d9b';
  const spec=FOCUSES[focus],f=spec.log?Math.log1p:x=>x;
  let t=Math.max(0,Math.min(1,(f(value)-f(spec.range[0]))/(f(spec.range[1])-f(spec.range[0]))));
  if(spec.reverse)t=1-t;
  const stops=spec.palette==='diverging'?[[35,118,122],[248,239,212],[177,58,36]]:[[247,231,175],[227,158,74],[153,53,37]];
  const i=t<=.5?0:1,u=i===0?t*2:(t-.5)*2;
  return `rgb(${stops[i].map((a,j)=>Math.round(a+(stops[i+1][j]-a)*u)).join(',')})`;
}
// Text uses a darker directional hue so small changes remain readable.
export function areaTextColor(value,focus){
  if(!Number.isFinite(value)||focus==='none'||value===0&&FOCUSES[focus].palette==='diverging')return '#5a6d68';
  if(COMBINED_VIEWS[focus])return ['#465351','#86511c','#295e7e','#684779'][value];
  if(FOCUSES[focus].palette==='diverging')return value>0?'#23767a':'#a63824';
  return `color-mix(in srgb, ${areaColor(value,focus)} 55%, #30251d)`;
}
export function pointInRing([x,y],ring){
  let inside=false;
  for(let i=0,j=ring.length-1;i<ring.length;j=i++){
    const [xi,yi]=ring[i],[xj,yj]=ring[j];
    if(((yi>y)!==(yj>y))&&(x<(xj-xi)*(y-yi)/(yj-yi)+xi))inside=!inside;
  }
  return inside;
}
export function areaAt(point,features){
  return features.find(f=>{
    const polys=f.geometry.type==='Polygon'?[f.geometry.coordinates]:f.geometry.coordinates;
    return polys.some(rings=>pointInRing(point,rings[0])&&!rings.slice(1).some(r=>pointInRing(point,r)));
  })?.properties.zip||null;
}

// Stable interior anchor: widest interior scanline segment in the largest polygon.
// Scanline pairing respects holes and keeps the marker inside concave ZIPs.
export function areaAnchor(feature){
  const polys=feature.geometry.type==='Polygon'?[feature.geometry.coordinates]:feature.geometry.coordinates;
  const size=r=>Math.abs(r.reduce((s,p,i)=>{const q=r[(i+1)%r.length];return s+p[0]*q[1]-q[0]*p[1];},0));
  const rings=polys.slice().sort((a,b)=>size(b[0])-size(a[0]))[0];
  const ys=rings[0].map(p=>p[1]),lo=Math.min(...ys),hi=Math.max(...ys);
  let best=null,width=-1;
  for(let k=1;k<40;k++){
    const y=lo+(hi-lo)*k/40,xs=[];
    for(const ring of rings)for(let i=0,j=ring.length-1;i<ring.length;j=i++){
      const a=ring[j],b=ring[i];if((a[1]>y)!==(b[1]>y))xs.push(a[0]+(y-a[1])*(b[0]-a[0])/(b[1]-a[1]));
    }
    xs.sort((a,b)=>a-b);
    for(let i=0;i+1<xs.length;i+=2)if(xs[i+1]-xs[i]>width){width=xs[i+1]-xs[i];best=[(xs[i]+xs[i+1])/2,y];}
  }
  return best||rings[0][0];
}
