// ZIP measures shown in the profile table and returned by the agent tools.
// One definition keeps the page and the tools reporting identical numbers.
const fixed=(v,d=0)=>Number.isFinite(v)?v.toLocaleString('en-US',{maximumFractionDigits:d,minimumFractionDigits:d}):'—';
const signed=(v,d)=>Number.isFinite(v)?(v>0?'+':v<0?'−':'')+fixed(Math.abs(v),d):'—';
import {PERIODS} from './place_area_math.mjs';
const acs=a=>a?.acs_year?`ACS ${a.acs_year-4}–${a.acs_year}`:'ACS unavailable';

// `focus` names the map layer that shares the measure's colour scale.
export const ZIP_MEASURES=[
  {key:'listings',label:'Yelp listings',term:'listings',unit:'businesses',value:a=>a.business_inventory,format:v=>fixed(v),period:()=>'January 2022 archive'},
  {key:'reviews',label:'Reviews',term:'reviews',unit:'reviews',value:a=>a.late?.reviews,format:v=>fixed(v),period:()=>PERIODS.level},
  {key:'engagement',label:'Business engagement',term:'engagement',focus:'activity',unit:'reviews / km² / year',value:a=>a.annual_review_density,format:v=>fixed(v),period:()=>`${PERIODS.level} · reviews / km² / year`},
  {key:'engagement_change',label:'Change in business engagement',term:'engagement_change',focus:'decline',unit:'% change in review count',value:a=>a.growth_pct,format:v=>signed(v,1)+'%',period:()=>PERIODS.change},
  {key:'sentiment',label:'Average review sentiment',term:'sentiment',unit:'VADER compound, −1 to +1',value:a=>a.late?.sentiment,format:v=>fixed(v,3),period:()=>`${PERIODS.level} · VADER`},
  {key:'sentiment_vs_metro',label:'Sentiment change vs. rest of metro',term:'sentiment_vs_metro',focus:'experience',unit:'VADER points',value:a=>a.relative_sentiment_change,format:v=>signed(v,3),period:()=>PERIODS.change},
  {key:'access_discussion',label:'Access & parking discussion',term:'access_discussion',focus:'access',unit:'% of reviews',value:a=>a.access_share_pct,format:v=>fixed(v,1)+'%',period:()=>`${PERIODS.level} · praise and complaints`},
  {key:'income',label:'Median household income',term:'income',focus:'income',unit:'US dollars (nominal)',value:a=>a.median_income,moe:a=>a.income_moe,format:v=>'$'+fixed(v),period:acs},
  {key:'poverty',label:'Population below poverty',term:'poverty',focus:'poverty',unit:'% of poverty-status population',value:a=>a.poverty_pct,format:v=>fixed(v,1)+'%',period:acs},
  {key:'area',label:'Land and water area',term:'area',unit:'km²',value:a=>a.area_km2,format:v=>fixed(v,1)+' km²',period:()=>'ZCTA boundary'}
];

const median=values=>{const v=values.slice().sort((x,y)=>x-y),m=v.length>>1;return v.length?(v.length%2?v[m]:(v[m-1]+v[m])/2):null;};

// One row per measure: value, city median, rank (1 = highest) and position (0 = lowest, 1 = highest).
export function zipProfile(cityAreas,zip){
  const area=cityAreas.find(a=>a.zip===zip)??null;
  return ZIP_MEASURES.map(m=>{
    const values=cityAreas.map(m.value).filter(Number.isFinite),v=area?m.value(area):null,ok=Number.isFinite(v);
    const moe=ok&&m.moe&&Number.isFinite(m.moe(area))?m.moe(area):null;
    return {measure:m,value:ok?v:null,moe,median:values.length?median(values):null,compared:values.length,
      rank:ok?values.filter(x=>x>v).length+1:null,
      position:ok&&values.length>1?values.filter(x=>x<v).length/(values.length-1):null,
      period:m.period(area)};
  });
}
