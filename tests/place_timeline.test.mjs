import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import {DEFAULT_TIME,applyTime,areaMeasures,windows,windowLabel,timeLabels,zipSeries,parsePeriod,periodLabel,periodCount} from '../src/place_timeline.mjs';
const read=p=>JSON.parse(readFileSync(new URL('../web/'+p,import.meta.url),'utf8'));
const timeline=read('place-timeline.json');
const fresh=()=>read('place-areas.json');

test('recomputing the default windows matches the published ZIP measures',()=>{
  const areas=fresh();let checked=0;
  for(const city of areas.cities)for(const a of city.areas){
    const m=areaMeasures(timeline,city.id,a.zip,a.area_km2,{...DEFAULT_TIME,to:28});
    assert.equal(m.late.reviews,a.late.reviews,a.zip);assert.equal(m.early.reviews,a.early.reviews,a.zip);
    for(const k of ['growth_pct','relative_sentiment_change','annual_review_density','access_share_pct']){
      if(a[k]===null){assert.equal(m[k],null,`${a.zip} ${k}`);continue;}
      assert.ok(Math.abs(m[k]-a[k])<1e-3*Math.max(1,Math.abs(a[k])),`${a.zip} ${k}: ${m[k]} vs ${a[k]}`);
    }
    checked++;
  }
  assert.equal(checked,196);
});

test('the default setting restores published values exactly, and other settings change them',()=>{
  const areas=fresh(),original=JSON.stringify(areas.cities);
  applyTime(areas,timeline,{...DEFAULT_TIME,mode:'snapshot',at:18});
  assert.notEqual(JSON.stringify(areas.cities),original);
  assert.equal(areas.time.labels.level,'Q3 2016');assert.equal(areas.time.labels.change,'Q3 2015 → Q3 2016');
  applyTime(areas,timeline,DEFAULT_TIME);
  assert.equal(JSON.stringify(areas.cities),original);
  assert.equal(areas.time.labels.change,'2012–2014 → 2019–2021');
});

test('windows, labels and minimums follow the grain',()=>{
  assert.deepEqual(windows(timeline,DEFAULT_TIME),{base:[0,35],level:[84,119]});
  assert.deepEqual(windows(timeline,{mode:'snapshot',grain:'month',smooth:3,at:30}),{level:[28,30],base:[16,18]});
  assert.equal(windowLabel(timeline,[0,35]),'2012–2014');assert.equal(windowLabel(timeline,[27,29]),'Q2 2014');
  assert.equal(windowLabel(timeline,[28,30]),'May–Jul 2014');assert.equal(windowLabel(timeline,[46,48]),'Nov 2015–Jan 2016');
  assert.equal(timeLabels(timeline,{mode:'snapshot',grain:'quarter',at:5}).minimum,50);
  assert.equal(timeLabels(timeline,{mode:'snapshot',grain:'month',smooth:12,at:40}).minimum,100);
  assert.equal(periodCount(timeline,'quarter'),40);assert.equal(periodLabel(timeline,'month',119),'Dec 2021');
});

test('the first year has no earlier period, and limited data stays null',()=>{
  const city=timeline.cities[0],zip=Object.keys(city.areas)[0];
  const m=areaMeasures(timeline,city.id,zip,10,{mode:'snapshot',grain:'quarter',at:2});
  assert.equal(m.growth_pct,null);assert.equal(m.relative_sentiment_change,null);
  assert.equal(timeLabels(timeline,{mode:'snapshot',grain:'quarter',at:2}).change,'no earlier period to compare');
  const quiet=areaMeasures(timeline,city.id,zip,10,{mode:'snapshot',grain:'month',smooth:1,at:0});
  if(quiet.late.reviews<50)assert.equal(quiet.annual_review_density,null);
});

test('month windows that cover no whole quarter have no access share',()=>{
  const city=timeline.cities[0],zip=Object.keys(city.areas)[0];
  assert.equal(areaMeasures(timeline,city.id,zip,10,{mode:'snapshot',grain:'month',smooth:1,at:40}).access_share_pct,null);
  assert.equal(timeLabels(timeline,{mode:'snapshot',grain:'month',smooth:1,at:40}).access,false);
});

test('series and period parsing',()=>{
  const city=timeline.cities.find(c=>c.id==='Philadelphia');
  const s=zipSeries(timeline,'Philadelphia','19134',{grain:'quarter'});
  assert.equal(s.length,40);assert.equal(s[0].label,'Q1 2012');
  assert.equal(s.reduce((n,p)=>n+p.reviews,0),city.areas['19134'].n.reduce((a,b)=>a+b,0));
  assert.equal(parsePeriod(timeline,'quarter','2016Q3'),18);assert.equal(parsePeriod(timeline,'quarter','2016-Q3'),18);
  assert.equal(parsePeriod(timeline,'month','2016-07'),54);assert.equal(parsePeriod(timeline,'quarter','2019'),28);
  assert.equal(parsePeriod(timeline,'quarter','2024'),null);
});
