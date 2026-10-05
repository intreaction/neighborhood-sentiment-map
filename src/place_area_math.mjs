// Area colors describe the existing ZIP analysis, never inferred block-level values.
// Category IDs are color lookups, not an ordered need score.
export const COMBINED_CATEGORIES=[
  {label:'Lower poverty · stable / growing',color:'#e3e5e6'},
  {label:'Lower poverty · declining',color:'#d98b39'},
  {label:'Higher poverty · stable / growing',color:'#5992b5'},
  {label:'Higher poverty · declining',color:'#75578a'}
];
export const FOCUSES={
  activity:{label:'Reach active business areas',field:'annual_review_density',title:'Business engagement',unit:'reviews / km² / year',period:'2019–2021 · annual average',note:'Yelp reviews per square kilometer, counting water inside the boundary. It can\'t see visits or revenue.',range:[0,3000],log:true,ends:['0','3,000+'],palette:'sequential'},
  income:{label:'Support lower-income areas',field:'median_income',title:'Median household income',unit:'historical dollars',period:'Baseline ACS · 2007–2011 / 2008–2012',note:'Warmer areas had lower household income. These are older ZIP estimates of residents, so they may not match reviewers or today.',range:[20000,100000],reverse:true,ends:['$100k+','$20k or less'],palette:'sequential'},
  poverty:{label:'Support lower-income areas',field:'poverty_pct',title:'Population below poverty',unit:'% of poverty-status population',period:'Baseline ACS · 2007–2011 / 2008–2012',note:'Warmer areas had a higher poverty rate. The estimates describe residents. Reviewers may live anywhere.',range:[0,50],ends:['0%','50%+'],palette:'sequential'},
  decline:{label:'Explore declining activity',field:'growth_pct',title:'Change in business engagement',unit:'% change in review count',period:'2012–2014 → 2019–2021',note:'Warm means decline and teal means growth. Each period needs at least 100 reviews, or 50 if it is shorter than a year. Periods from 2020 on include COVID-19. Reviews starting or stopping does not mean a business opened or closed.',range:[-100,100],reverse:true,ends:['Growth +100% or more','Decline −100%'],palette:'diverging'},
  experience:{label:'Explore worsening experiences',field:'relative_sentiment_change',title:'Sentiment change vs. the city',unit:'VADER score difference',period:'2012–2014 → 2019–2021',note:'Warm means sentiment changed for the worse compared with the rest of the metro. It scores whole reviews, which are mostly about businesses. A ZIP can improve relative to the metro even when its own sentiment falls.',range:[-.15,.15],reverse:true,ends:['Better +0.15 or more','Worse −0.15 or less'],palette:'diverging'},
  access:{label:'Investigate access concerns',field:'access_share_pct',title:'Access & parking discussion',unit:'% of reviews mentioning access',period:'2019–2021 · existing keyword analysis',note:'Mentions of parking, walking, transit and accessibility, counting praise and complaints alike. A high rate does not mean people are unhappy. Needs at least 100 reviews.',range:[0,15],ends:['0%','15%+'],palette:'sequential'},
  none:{label:'No heatmap',title:'Street map',note:'Choose a focus to color the map.',period:'',range:[0,1],ends:['',''],palette:'sequential'}
};
// Shared measure definitions keep legends, cards, exports and classification aligned.
export const COMBINED_MEASURES={
  poverty:{focus:'poverty',field:'poverty_pct',threshold:20,operator:'>=',low:'Lower poverty',high:'Higher poverty',short:'Poverty',lowRule:'< 20%',highRule:'≥ 20%',note:'We use a 20% poverty cutoff to explore. It is not an official need designation.'},
  decline:{focus:'decline',field:'growth_pct',threshold:0,operator:'<',low:'Stable / growing',high:'Declining',short:'Decline',lowRule:'≥ 0%',highRule:'< 0%',note:'Activity counts reviews, so a drop does not mean businesses closed. The later period includes COVID-19.'},
  experience:{focus:'experience',field:'relative_sentiment_change',threshold:0,operator:'<',low:'At / above city',high:'Below city',short:'Sentiment',lowRule:'≥ 0 VADER',highRule:'< 0 VADER',note:'Sentiment change is measured against the rest of the city, so the ZIP\'s own sentiment may not have fallen.'},
  access:{focus:'access',field:'access_share_pct',threshold:5,operator:'>=',low:'Less discussion',high:'More discussion',short:'Access',lowRule:'< 5%',highRule:'≥ 5%',note:'We use a 5% mention cutoff to explore. Access discussion counts praise and complaints alike.'}
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
// The map timeline changes which periods the review measures describe; legends and cards read these.
export const PERIODS={level:'2019–2021',base:'2012–2014',change:'2012–2014 → 2019–2021'};
export function applyPeriodLabels(labels){
  Object.assign(PERIODS,labels);
  FOCUSES.activity.period=`${PERIODS.level} · annual rate`;
  FOCUSES.decline.period=FOCUSES.experience.period=PERIODS.change;
  FOCUSES.access.period=`${PERIODS.level} · keyword analysis`;
  for(const [key,view] of Object.entries(COMBINED_VIEWS))FOCUSES[key].period=[...new Set(view.measures.map(m=>FOCUSES[COMBINED_MEASURES[m].focus].period))].join('; ');
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
  return rampColor(t,spec.palette==='diverging');
}
// Shared map ramps: t in [0,1], light to dark (sequential) or teal–cream–red (diverging).
export function rampColor(t,diverging=false){
  const stops=diverging?[[35,118,122],[248,239,212],[177,58,36]]:[[247,231,175],[227,158,74],[153,53,37]];
  t=Math.max(0,Math.min(1,t));
  const i=t<=.5?0:1,u=i===0?t*2:(t-.5)*2;
  return `rgb(${stops[i].map((a,j)=>Math.round(a+(stops[i+1][j]-a)*u)).join(',')})`;
}
// Text uses a darker directional hue so small changes remain readable.
export function areaTextColor(value,focus){
  if(!Number.isFinite(value)||focus==='none'||value===0&&FOCUSES[focus].palette==='diverging')return 'var(--c-5a6d68)';
  if(COMBINED_VIEWS[focus])return ['var(--c-465351)','var(--c-86511c)','var(--c-295e7e)','var(--c-684779)'][value];
  if(FOCUSES[focus].palette==='diverging')return value>0?'var(--c-23767a)':'var(--c-a63824)';
  return `color-mix(in srgb, ${areaColor(value,focus)} 55%, var(--c-30251d))`;
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
