// Map timeline: rebuild the ZIP measures for any period from monthly sums in place-timeline.json.
// The same rules as build_place_areas.py apply: review-weighted VADER, change against the rest of the
// metro, and a minimum review count per period (100 for a year or longer, 50 for shorter periods).
const MONTHS=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
export const DEFAULT_TIME={mode:'compare',grain:'quarter',smooth:3,at:39,from:0,to:28,length:12};
export const SMOOTHING=[1,3,12];

const startOf=t=>{const [y,m]=t.start.split('-').map(Number);return {year:y,month:m-1};};
export function periodCount(timeline,grain){return grain==='quarter'?timeline.months/3:timeline.months;}
export function periodLabel(timeline,grain,i){
  const {year,month}=startOf(timeline);
  if(grain==='quarter'){const q=month/3+i;return `Q${q%4+1} ${year+Math.floor(q/4)}`;}
  const m=month+i;return `${MONTHS[m%12]} ${year+Math.floor(m/12)}`;
}
// Month index of a period's first month.
const unit=grain=>grain==='quarter'?3:1;
export function isDefault(s){return Object.keys(DEFAULT_TIME).every(k=>k==='at'||k==='smooth'||s[k]===DEFAULT_TIME[k]);}

// Inclusive month ranges: `level` is the period being described, `base` the period it is compared with.
export function windows(timeline,setting){
  const u=unit(setting.grain);
  if(setting.mode==='snapshot'){
    const end=setting.grain==='quarter'?setting.at*3+2:setting.at;
    const span=setting.grain==='quarter'?3:setting.smooth;
    const level=[end-span+1,end];
    return {level,base:[level[0]-12,level[1]-12]};
  }
  return {base:[setting.from*u,(setting.from+setting.length)*u-1],level:[setting.to*u,(setting.to+setting.length)*u-1]};
}
const valid=(timeline,[a,b])=>a>=0&&b<timeline.months&&a<=b;
export function minimumFor(timeline,[a,b]){return b-a+1>=12?timeline.minimum_reviews.year_or_longer:timeline.minimum_reviews.shorter;}

export function windowLabel(timeline,[a,b]){
  const {year,month}=startOf(timeline),y=i=>year+Math.floor((month+i)/12),m=i=>(month+i)%12;
  if(m(a)===0&&m(b)===11)return y(a)===y(b)?String(y(a)):`${y(a)}–${y(b)}`;
  const q=i=>`Q${Math.floor(m(i)/3)+1} ${y(i)}`;
  if(m(a)%3===0&&m(b)%3===2)return a+2===b?q(a):`${q(a)}–${q(b)}`;
  if(a===b)return `${MONTHS[m(a)]} ${y(a)}`;
  return y(a)===y(b)?`${MONTHS[m(a)]}–${MONTHS[m(b)]} ${y(a)}`:`${MONTHS[m(a)]} ${y(a)}–${MONTHS[m(b)]} ${y(b)}`;
}

const total=(arr,[a,b])=>{let s=0;for(let i=a;i<=b;i++)s+=arr[i];return s;};
function summary(cell,range){
  const n=total(cell.n,range),sum=total(cell.c,range);
  return {reviews:n,sentiment_sum:sum,sentiment:n?sum/n:null};
}
// Access counts exist by quarter only, so use the quarters that sit wholly inside the range.
function accessTotals(cell,[a,b]){
  let mentions=0,reviews=0,quarters=0;
  for(let q=Math.ceil(a/3);q*3+2<=b;q++){mentions+=cell.an[q];reviews+=cell.ad[q];quarters++;}
  return quarters?{mentions,reviews}:null;
}
function compare(early,late,metroEarly,metroLate,minimum){
  if(Math.min(early.reviews,late.reviews)<minimum)return {growth_pct:null,sentiment_change:null,relative_sentiment_change:null};
  const out={growth_pct:100*(late.reviews/early.reviews-1),sentiment_change:late.sentiment-early.sentiment,relative_sentiment_change:null};
  const n0=metroEarly.reviews-early.reviews,n1=metroLate.reviews-late.reviews;
  if(Math.min(n0,n1)>=minimum)out.relative_sentiment_change=out.sentiment_change-((metroLate.sentiment_sum-late.sentiment_sum)/n1-(metroEarly.sentiment_sum-early.sentiment_sum)/n0);
  return out;
}

// Measures for one ZIP; null wherever a period falls outside the data or below the minimum.
export function areaMeasures(timeline,cityId,zip,areaKm2,setting){
  const city=timeline.cities.find(c=>c.id===cityId),cell=city?.areas[zip];
  const {level,base}=windows(timeline,setting);
  const empty={reviews:0,sentiment_sum:0,sentiment:null};
  if(!cell||!valid(timeline,level))return {early:empty,late:empty,growth_pct:null,sentiment_change:null,relative_sentiment_change:null,annual_review_density:null,access_mentions:null,access_share_pct:null};
  const minimum=minimumFor(timeline,level),late=summary(cell,level),months=level[1]-level[0]+1;
  const early=valid(timeline,base)?summary(cell,base):empty;
  const changes=valid(timeline,base)?compare(early,late,summary(city.metro,base),summary(city.metro,level),minimum):{growth_pct:null,sentiment_change:null,relative_sentiment_change:null};
  const access=accessTotals(cell,level);
  return {early,late,...changes,
    annual_review_density:late.reviews>=minimum&&areaKm2>0?late.reviews/(months/12)/areaKm2:null,
    access_mentions:access?.mentions??null,access_share_pct:access&&access.reviews>=minimum?100*access.mentions/access.reviews:null};
}

export function timeLabels(timeline,setting){
  const {level,base}=windows(timeline,setting),ok=valid(timeline,level),baseOk=valid(timeline,base);
  const levelText=ok?windowLabel(timeline,level):'outside the data';
  return {level:levelText,base:baseOk?windowLabel(timeline,base):'no earlier period',change:baseOk&&ok?`${windowLabel(timeline,base)} → ${levelText}`:'no earlier period to compare',
    minimum:ok?minimumFor(timeline,level):null,access:ok&&Math.ceil(level[0]/3)*3+2<=level[1]};
}

// Rewrite the review-based fields of every area in place so the map, profile and tools share one state.
// The default setting restores the published values, so the page matches the findings and slides exactly.
export function applyTime(areaData,timeline,setting){
  areaData.__published??=areaData.cities.map(c=>c.areas.map(a=>({...a})));
  areaData.cities.forEach((city,ci)=>city.areas.forEach((area,ai)=>{
    Object.assign(area,isDefault(setting)?areaData.__published[ci][ai]:areaMeasures(timeline,city.id,area.zip,area.area_km2,setting));
  }));
  areaData.time={setting:{...setting},labels:isDefault(setting)?{level:'2019–2021',base:'2012–2014',change:'2012–2014 → 2019–2021',minimum:100,access:true}:timeLabels(timeline,setting)};
  return areaData.time;
}

// One ZIP's series at the chosen grain, with the rest of its metro for comparison.
export function zipSeries(timeline,cityId,zip,setting){
  const city=timeline.cities.find(c=>c.id===cityId),cell=city?.areas[zip];
  if(!cell)return [];
  const n=periodCount(timeline,setting.grain),u=unit(setting.grain),span=setting.grain==='month'?setting.smooth:3;
  return Array.from({length:n},(_,i)=>{
    const end=i*u+u-1,range=[Math.max(0,end-span+1),end];
    const z=summary(cell,range),m=summary(city.metro,range),restN=m.reviews-z.reviews;
    const minimum=minimumFor(timeline,range);
    return {index:i,label:periodLabel(timeline,setting.grain,i),reviews:z.reviews,
      sentiment:z.reviews>=minimum?z.sentiment:null,metro_sentiment:restN>=minimum?(m.sentiment_sum-z.sentiment_sum)/restN:null};
  });
}

// Parse "2016", "2016Q3", "2016-Q3" or "2016-07" into a period index at the given grain.
export function parsePeriod(timeline,grain,text){
  const s=String(text).trim().toUpperCase(),{year,month}=startOf(timeline);
  let y,m;
  let k=s.match(/^(\d{4})-?Q([1-4])$/);if(k){y=+k[1];m=(+k[2]-1)*3;}
  k=s.match(/^(\d{4})-(\d{1,2})$/);if(k){y=+k[1];m=+k[2]-1;}
  k=s.match(/^(\d{4})$/);if(k){y=+k[1];m=0;}
  if(y===undefined)return null;
  const months=(y-year)*12+m-month,i=grain==='quarter'?Math.floor(months/3):months;
  return i>=0&&i<periodCount(timeline,grain)?i:null;
}
