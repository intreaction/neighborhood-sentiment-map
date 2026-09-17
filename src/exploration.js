const A={topic:'all',lag:4,window:4,minimum:30,outcome:'change',sort:'funding',example:'access',basis:'total',populationMinimum:500};
const REV=__REVIEWS__;
const POP=D.population.records;
const residentMoney=v=>v==null?'Unavailable':new Intl.NumberFormat('en-US',{style:'currency',currency:'USD',maximumFractionDigits:2}).format(v);
const fundingUnits=()=>A.basis==='resident'?'Funding per 2020 resident':'Total recorded funding';
const fundingFormat=v=>A.basis==='resident'?residentMoney(v):money(v);
const populationOf=z=>POP[z]?.population??null;
const maxPerResident=Math.max(1,...GEO.features.flatMap(f=>f.properties.i.map(v=>perResident(v,populationOf(f.properties.zip))??0)).map(Math.abs));
__ANALYSIS_MATH__
let viewCache=new Map(),currentRows=[],exportUrl=null;
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const themeName=()=>A.topic==='all'?'All reviews':REV?.topics[A.topic]?.label||'All reviews';
const rawTopicCell=(z,q,t)=>REV?.panel[z]?.[D.quarters[q]]?.topics[t]||[0,0,0];
function zipView(zip){
  const key=`z:${zip}:${A.topic}:${A.minimum}`;if(viewCache.has(key))return viewCache.get(key);
  const p=features[zip].properties;
  let result;
  if(A.topic==='all')result={sent:p.s.map((s,i)=>p.n[i]>=A.minimum?s:null),n:p.n,neg:p.g.map((g,i)=>p.n[i]>=A.minimum?g:null),inv:p.i};
  else{const cells=D.quarters.map((_,q)=>rawTopicCell(zip,q,A.topic));result={sent:cells.map(c=>c[0]>=A.minimum?c[1]/c[0]:null),n:cells.map(c=>c[0]),neg:cells.map(c=>c[0]>=A.minimum?100*c[2]/c[0]:null),inv:p.i};}
  viewCache.set(key,result);return result;
}
function cityView(city){
  const key=`m:${city}:${A.topic}:${A.minimum}`;if(viewCache.has(key))return viewCache.get(key);
  const base=D.series[city];let result;
  if(A.topic==='all')result={...base,sent:base.sent.map((s,i)=>base.n[i]>=A.minimum?s:null)};
  else{const zips=Object.keys(D.zipMetro).filter(z=>D.zipMetro[z]===city);const cells=D.quarters.map((_,q)=>zips.reduce((a,z)=>{const c=rawTopicCell(z,q,A.topic);return a.map((v,i)=>v+c[i]);},[0,0,0]));result={sent:cells.map(c=>c[0]>=A.minimum?c[1]/c[0]:null),n:cells.map(c=>c[0]),neg:cells.map(c=>c[0]>=A.minimum?100*c[2]/c[0]:null),inv:base.inv};}
  viewCache.set(key,result);return result;
}
function comparisonRows(lag=A.lag){
  return cityFeatures.map(f=>{const z=f.properties.zip,a=zipView(z),population=populationOf(z),funding=fundingWindow(a.inv,S.q,lag,A.window),rate=perResident(funding,population,A.populationMinimum),xFunding=A.basis==='resident'?rate:funding,y=reviewOutcome(a.sent,S.q,A.outcome);return {zip:z,population,funding,rate,xFunding,y,n:a.n[S.q],sent:a.sent[S.q],change:reviewOutcome(a.sent,S.q,'change'),included:xFunding!=null&&y!=null,status:funding==null?'Funding history unavailable':A.basis==='resident'&&rate==null?'Population missing / zero / below minimum':y==null?'Insufficient review coverage':'Included'};});
}

function setTopic(topic){A.topic=topic;viewCache.clear();$('reviewLens').value=topic;if(topic!=='all'){A.example=topic;$('exampleTopic').value=topic;}render();}
function plotFrame(id,height){const svg=$(id),width=Math.max(260,svg.getBoundingClientRect().width);svg.setAttribute('viewBox',`0 0 ${width} ${height}`);svg.replaceChildren();return {svg,width,height,L:58,R:18,T:18,B:42};}
function plotText(svg,x,y,text,extra={}){svg.append(node('text',{x,y,fill:'#667671','font-size':10,...extra},text));}
function emptyPlot(svg,w,h,text){plotText(svg,w/2,h/2,text,{'text-anchor':'middle'});}
function drawScatter(rows){
  const {svg,width:w,height:h,L,R,T,B}=plotFrame('scatter',340),data=rows.filter(r=>r.included);
  if(!data.length){emptyPlot(svg,w,h,'No ZIPs meet this window and review threshold.');return;}
  const xs=data.map(r=>signedLog(r.xFunding)),ys=data.map(r=>r.y);let x0=Math.min(0,...xs),x1=Math.max(0,...xs),y0=Math.min(0,...ys),y1=Math.max(0,...ys);
  if(x0===x1){x0-=1;x1+=1;}if(y0===y1){y0-=.05;y1+=.05;}const yp=(y1-y0)*.15;y0-=yp;y1+=yp;
  const x=v=>L+(v-x0)/(x1-x0)*(w-L-R),y=v=>T+(y1-v)/(y1-y0)*(h-T-B);
  for(let i=0;i<5;i++){const v=y0+(y1-y0)*i/4;svg.append(node('line',{x1:L,x2:w-R,y1:y(v),y2:y(v),stroke:'#e2e5dc'}));plotText(svg,L-8,y(v)+3,v.toFixed(2),{'text-anchor':'end'});}
  svg.append(node('line',{x1:L,x2:w-R,y1:y(0),y2:y(0),stroke:'#9dab9e','stroke-dasharray':'4 4'}));
  for(let i=0;i<4;i++){const v=x0+(x1-x0)*i/3;plotText(svg,x(v),h-B+17,fundingFormat(Math.sign(v)*Math.expm1(Math.abs(v))),{'text-anchor':i===0?'start':i===3?'end':'middle'});}
  plotText(svg,w/2,h-3,fundingUnits()+' · signed log scale',{'text-anchor':'middle'});
  plotText(svg,L,T-6,A.outcome==='change'?'Annual sentiment change':'Mean review sentiment');
  for(const r of data){const circle=node('circle',{cx:x(signedLog(r.xFunding)),cy:y(r.y),r:r.zip===S.zip?7:5,fill:r.y<0&&A.outcome==='change'?'#b66740':'#146e64','fill-opacity':.65,stroke:r.zip===S.zip?'#243d3b':'#fffefa','stroke-width':r.zip===S.zip?2:1,class:'data-point','data-zip':r.zip,tabindex:0,role:'button','aria-label':`Select ZIP ${r.zip}, funding ${fundingFormat(r.xFunding)}, outcome ${score(r.y)}`});
    const activate=()=>selectZip(r.zip);circle.addEventListener('click',activate);circle.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});circle.addEventListener('pointermove',ev=>showTip(ev,`<b>ZIP ${r.zip}</b><br>${fundingFormat(r.xFunding)} ${A.basis==='resident'?'per 2020 resident':'earlier funding'}<br>${r.population==null?'No population count':fmt.format(r.population)+' residents (2020)'}<br>${score(r.y)} ${A.outcome==='change'?'annual change':'sentiment'}<br><small>${fmt.format(r.n)} matching reviews</small>`));circle.addEventListener('pointerleave',hideTip);svg.append(circle);
  }
}
function drawLags(){
  const {svg,width:w,height:h,L,R,T,B}=plotFrame('lagChart',220);
  const every=Array.from({length:13},(_,lag)=>comparisonRows(lag));
  const cohort=cityFeatures.map(f=>f.properties.zip).filter(z=>every.every(rows=>rows.find(r=>r.zip===z)?.included));
  const rs=every.map(rows=>correlation(rows.filter(r=>cohort.includes(r.zip)).map(r=>[signedLog(r.xFunding),r.y])));
  const x=i=>L+(i+.5)/13*(w-L-R),y=v=>T+(1-v)/2*(h-T-B);
  [-1,0,1].forEach(v=>{svg.append(node('line',{x1:L,x2:w-R,y1:y(v),y2:y(v),stroke:v===0?'#9dab9e':'#e2e5dc'}));plotText(svg,L-10,y(v)+3,v.toFixed(1),{'text-anchor':'end'});});
  const bw=(w-L-R)/13*.65;
  rs.forEach((r,i)=>{const g=node('g',{role:'button',tabindex:0,'aria-label':`Set funding lag to ${i} quarters${r==null?', correlation unavailable':', correlation '+r.toFixed(3)}`,cursor:'pointer'});g.append(node('rect',{x:x(i)-bw/2-3,y:T,width:bw+6,height:h-T-B,fill:i===A.lag?'#e9eee4':'transparent',stroke:i===A.lag?'#91aa9c':'none',rx:3}));if(r!=null)g.append(node('rect',{x:x(i)-bw/2,y:Math.min(y(r),y(0)),width:bw,height:Math.max(1,Math.abs(y(r)-y(0))),fill:r<0?'#b66740':'#146e64'}));else plotText(g,x(i),y(0)-8,'—',{'text-anchor':'middle'});const activate=()=>{A.lag=i;$('lag').value=i;renderAnalysis();};g.addEventListener('click',activate);g.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();activate();}});g.addEventListener('pointermove',e=>showTip(e,`<b>${i} quarters lag</b><br>${r==null?'Correlation unavailable':'r = '+r.toFixed(3)}<br><small>${cohort.length} ZIPs in fixed cohort</small>`));g.addEventListener('pointerleave',hideTip);svg.append(g);if(w>450||i%4===0)plotText(svg,x(i),h-B+18,i+'q',{'text-anchor':'middle'});});
  $('lagExplanation').textContent=`${cohort.length} ZIPs with complete history at all 13 lags. Correlations use signed-log ${A.basis==='resident'?'funding per 2020 resident':'total funding'} and ${A.outcome==='change'?'annual sentiment change':'sentiment level'}. ${cohort.length<3?'Move the review quarter later or lower the review threshold to obtain a comparable cohort.':'The vertical scale is fixed from −1 to +1.'}`;
}
function topicSnapshot(){const zips=S.zip?[S.zip]:Object.keys(D.zipMetro).filter(z=>D.zipMetro[z]===S.city),topics=Object.fromEntries(Object.keys(REV?.topics||{}).map(k=>[k,[0,0,0]])),stars=[0,0,0,0,0];for(const z of zips){const c=REV?.panel[z]?.[D.quarters[S.q]];if(!c)continue;c.stars.forEach((v,i)=>stars[i]+=v);for(const [t,v] of Object.entries(c.topics))v.forEach((n,i)=>topics[t][i]+=n);}return {topics,stars,total:stars.reduce((a,b)=>a+b,0)};}
function renderReviews(){
  $('reviewScope').textContent=`${S.zip?'ZIP '+S.zip:D.metros[S.city].label} · ${qlabel(S.q)}`;
  if(!REV){$('topicUnavailable').hidden=false;return;}
  const snap=topicSnapshot();$('topicBars').replaceChildren();
  for(const [key,t] of Object.entries(REV.topics)){const c=snap.topics[key],share=snap.total?100*c[0]/snap.total:0,b=document.createElement('button');b.className='topic-row';b.setAttribute('aria-pressed',String(key===A.topic));b.setAttribute('aria-label','Filter reviews: '+t.label);b.title=t.hint;b.innerHTML=`<span class="topic-row-top"><strong>${safe(t.label)}</strong><span>${share.toFixed(1)}% · ${fmt.format(c[0])} reviews</span></span><span class="topic-track"><i style="width:${share}%"></i></span><small>Whole-review sentiment: ${c[0]>=A.minimum?score(c[1]/c[0]):'below '+A.minimum+' reviews'}</small>`;b.onclick=()=>setTopic(key);$('topicBars').append(b);}
  $('ratingBars').innerHTML=snap.stars.map((n,i)=>`<div class="ratings-row"><span>${i+1} star${i?'s':''}</span><span class="topic-track"><i style="width:${snap.total?100*n/snap.total:0}%"></i></span><span>${snap.total?(100*n/snap.total).toFixed(1):'0'}%</span></div>`).join('');
  $('ratingSummary').textContent=snap.total?`${fmt.format(snap.total)} reviews · average ${(snap.stars.reduce((s,n,i)=>s+n*(i+1),0)/snap.total).toFixed(2)} stars. ${fmt.format(REV.nReviews)} reviews were reconciled with their existing sentiment scores for the text analysis.`:'No reviews in this area and quarter.';
  renderExamples();
}
function renderExamples(){if(!REV)return;const year=D.quarters[S.q].slice(0,4);$('excerptScope').textContent=`${D.metros[S.city].label} · ${year} · ${REV.topics[A.example].label}. Citywide examples from the whole year, regardless of selected ZIP or quarter.`;const candidates=REV.examples.filter(e=>e.metro===S.city&&e.quarter.startsWith(year)&&e.topic===A.example),picked=[];for(const p of ['negative','neutral','positive']){const e=candidates.find(e=>e.polarity===p);if(e)picked.push(e);}$('examples').replaceChildren();if(!picked.length){$('examples').innerHTML='<p class="empty-panel">No sampled excerpts for this city, year and theme.</p>';return;}for(const e of picked){const card=document.createElement('article');card.className='quote-card';card.innerHTML=`<span class="pill">${safe(e.polarity)} whole-review score</span><blockquote></blockquote><div class="quote-meta">ZIP ${safe(e.zip)} · ${safe(e.quarter)} · ${e.stars} star${e.stars===1?'':'s'}<br>VADER ${score(e.compound)}</div>`;card.querySelector('blockquote').textContent=e.text;$('examples').append(card);}}
function renderLedger(rows){const sorted=rows.slice().sort((a,b)=>(b[A.sort==='funding'?'funding':A.sort==='rate'?'rate':'change']??-Infinity)-(a[A.sort==='funding'?'funding':A.sort==='rate'?'rate':'change']??-Infinity)||a.zip.localeCompare(b.zip));$('areaRows').innerHTML=sorted.map(r=>`<tr data-selected="${r.zip===S.zip}"><td><button data-select-zip="${r.zip}">ZIP ${r.zip}</button></td><td>${r.funding==null?'Unavailable':money(r.funding)}</td><td>${r.population==null?'Unavailable':fmt.format(r.population)}</td><td>${residentMoney(r.rate)}</td><td>${r.sent==null?'Unavailable':score(r.sent)}</td><td>${r.change==null?'Unavailable':score(r.change)}</td><td>${fmt.format(r.n)}</td><td>${r.status}</td></tr>`).join('');$('sortFunding').textContent='Funding window '+(A.sort==='funding'?'↓':'↕');$('sortChange').textContent='Annual change '+(A.sort==='change'?'↓':'↕');$('sortRate').textContent='Funding / resident '+(A.sort==='rate'?'↓':'↕');}
function renderAnalysis(){
  const scope=`${D.metros[S.city].label} · ${qlabel(S.q)} · ${themeName()} · ${fundingUnits()}`;document.querySelectorAll('.analysis-scope').forEach(e=>e.textContent=scope);
  $('lensNote').textContent=A.topic==='all'?`All business reviews · ${A.minimum}+ reviews per sentiment quarter`:`Keyword mentions of ${themeName().toLowerCase()} · whole-review sentiment · ${A.minimum}+ matching reviews`;
  for(const [id,value] of [['lag',A.lag],['window',A.window],['minimum',A.minimum]]){$(id).setAttribute('aria-valuetext',value+(id==='minimum'?' reviews':' quarters'));}
  $('lagReadout').textContent=A.lag+' quarters';$('windowReadout').textContent=A.window+' quarter'+(A.window===1?'':'s');$('minimumReadout').textContent=A.minimum;
  const end=S.q-A.lag,start=end-A.window+1,complete=start>=0;
  $('fundingDates').textContent=complete?D.quarters[start]+(end!==start?' → '+D.quarters[end]:''):'Before available history';
  const amount=fundingWindow(selected().inv,S.q,A.lag,A.window);$('windowAmount').textContent=amount==null?'Full window is unavailable':money(amount)+' · '+(S.zip?'selected ZIP':'entire city study area');$('gapLabel').textContent=A.lag?A.lag+' quarters later':'Same quarter';$('outcomeDates').textContent=D.quarters[S.q];$('outcomeDefinition').textContent=A.outcome==='level'?'Mean sentiment this quarter':S.q>=4?'Change from '+D.quarters[S.q-4]:'Prior-year comparison unavailable';
  const rows=comparisonRows(),included=rows.filter(r=>r.included),r=correlation(included.map(r=>[signedLog(r.xFunding),r.y]));currentRows=rows;
  $('correlation').textContent=r==null?'—':(r>0?'+':'')+r.toFixed(3);$('eligibleCount').textContent=included.length;$('excludedCount').textContent=rows.length-included.length;
  $('relationshipText').textContent=r==null?'Not enough usable variation to calculate a correlation. Adjust the quarter, funding window or review coverage.':`${Math.abs(r)<.1?'Little linear association appears':r>0?'Higher recorded funding aligns with higher outcomes':'Higher recorded funding aligns with lower outcomes'} in this snapshot, using signed-log ${A.basis==='resident'?'funding per 2020 resident':'total funding'} and ${A.outcome==='change'?'annual sentiment change':'sentiment level'}.${included.length<10?' Fewer than ten ZIPs are included; this comparison is especially sensitive to individual places.':''}`;
  drawScatter(rows);drawLags();renderReviews();renderLedger(rows);renderPopulation();
}
function renderCapitalEfficiency(){
  if(!$('efficiencyRows')) return;
  const radius = $('effRadius') ? $('effRadius').value : '500';
  const income = $('effIncome') ? $('effIncome').value : 'All';
  const rows = (D.capitalEfficiency || []).filter(r =>
    String(r.radius_m) === radius &&
    r.income_group === income &&
    r.metric === 'reviews'
  );
  if(!rows.length){
    $('efficiencyRows').innerHTML = '<tr><td colspan="10" style="text-align:center; padding:18px; color:var(--muted);">No matched data available for this radius and income tier combination.</td></tr>';
    return;
  }
  // Plan invariant: Flagged rows (low_support = true, N < 20) MUST be suppressed from ranking comparisons.
  // Sort supported (non-flagged) rows descending by CE_abs; append flagged rows at the bottom.
  rows.sort((a, b) => {
    const flagA = a.low_support === true || a.low_support === 'True';
    const flagB = b.low_support === true || b.low_support === 'True';
    if (flagA !== flagB) return flagA ? 1 : -1;
    return (parseFloat(b.ce_abs_per_million) || 0) - (parseFloat(a.ce_abs_per_million) || 0);
  });
  $('efficiencyRows').innerHTML = rows.map(r => {
    const isFlag = r.low_support === true || r.low_support === 'True';
    const flagHtml = isFlag ? '<span style="color:#b66740; font-weight:600;">FLAG (N&lt;20)</span>' : '<span style="color:#146e64;">OK</span>';
    const did = parseFloat(r.did_per_pair) || 0;
    const didStr = (did > 0 ? '+' : '') + did.toFixed(2);
    const netVol = parseFloat(r.net_volume_gain) || 0;
    const netVolStr = (netVol > 0 ? '+' : '') + netVol.toFixed(1);
    const ceAbs = parseFloat(r.ce_abs_per_million);
    const ceAbsStr = isNaN(ceAbs) ? 'N/A' : (ceAbs > 0 ? '+' : '') + ceAbs.toFixed(2);
    const ceRel = parseFloat(r.ce_rel_pct_per_million);
    const ceRelStr = isNaN(ceRel) ? 'N/A' : (ceRel > 0 ? '+' : '') + ceRel.toFixed(2) + '%';
    const ceNorm = parseFloat(r.ce_norm_pct_per_million);
    const ceNormStr = isNaN(ceNorm) ? 'N/A' : (ceNorm > 0 ? '+' : '') + ceNorm.toFixed(2) + '%';

    return `<tr>
      <td><strong>${safe(r.project)}</strong><br><small style="color:var(--muted);">${safe(r.project_type)}</small></td>
      <td>${safe(r.city)}</td>
      <td>$${parseFloat(r.cost_millions).toFixed(1)}M</td>
      <td>${r.pairs}</td>
      <td style="color:${did < 0 ? 'var(--orange)' : 'inherit'};">${didStr}</td>
      <td style="color:${netVol < 0 ? 'var(--orange)' : 'inherit'};">${netVolStr}</td>
      <td><strong>${isFlag ? '<span style="color:var(--muted);">' + ceAbsStr + '</span>' : ceAbsStr}</strong></td>
      <td>${isFlag ? '<span style="color:var(--muted);">' + ceRelStr + '</span>' : ceRelStr}</td>
      <td>${isFlag ? '<span style="color:var(--muted);">' + ceNormStr + '</span>' : ceNormStr}</td>
      <td>${flagHtml}</td>
    </tr>`;
  }).join('');
}
function initializeAnalysis(){
  for(const [key,t] of Object.entries(REV?.topics||{})){$('reviewLens').add(new Option(t.label,key));$('exampleTopic').add(new Option(t.label,key));}
  $('reviewLens').onchange=e=>setTopic(e.target.value);$('exampleTopic').value=A.example;$('exampleTopic').onchange=e=>{A.example=e.target.value;renderExamples();};$('clearTopic').onclick=()=>setTopic('all');
  ['lag','window','minimum'].forEach(id=>$(id).addEventListener('input',e=>{A[id]=+e.target.value;hideTip();if(id==='minimum'){viewCache.clear();render();}else renderAnalysis();}));
  $('fundingBasis').onchange=e=>{A.basis=e.target.value;renderAnalysis();};$('populationMinimum').oninput=e=>{A.populationMinimum=+e.target.value;renderMap();renderLegend();renderAnalysis();};
  $('outcome').onchange=e=>{A.outcome=e.target.value;renderAnalysis();};$('sortFunding').onclick=()=>{A.sort='funding';renderLedger(currentRows);};$('sortRate').onclick=()=>{A.sort='rate';renderLedger(currentRows);};$('sortChange').onclick=()=>{A.sort='change';renderLedger(currentRows);};$('populationRows').onclick=e=>{const b=e.target.closest('[data-pop-city]');if(b)selectCity(b.dataset.popCity);};$('areaRows').onclick=e=>{const b=e.target.closest('[data-select-zip]');if(b)selectZip(b.dataset.selectZip);};
  $('downloadComparison').onclick=()=>{const end=S.q-A.lag,start=end-A.window+1;const columns=['city','zip','review_theme','review_quarter','funding_start','funding_end','lag_quarters','window_quarters','minimum_reviews','net_obligations','population_2020','funding_per_2020_resident','funding_basis','minimum_population','mean_sentiment','annual_change','matching_reviews','outcome','included','status'];const data=currentRows.map(r=>[S.city,r.zip,themeName(),D.quarters[S.q],start>=0?D.quarters[start]:'',end>=0?D.quarters[end]:'',A.lag,A.window,A.minimum,r.funding,r.population,r.rate,A.basis,A.populationMinimum,r.sent,r.change,r.n,A.outcome,r.included,r.status]);const csv=[columns,...data].map(row=>row.map(v=>'"'+String(typeof v==='number'&&!Number.isInteger(v)?Number(v.toFixed(6)):v??'').replace(/"/g,'""')+'"').join(',')).join('\r\n');if(exportUrl)URL.revokeObjectURL(exportUrl);exportUrl=URL.createObjectURL(new Blob([csv],{type:'text/csv;charset=utf-8'}));$('exportText').value=csv;$('exportSummary').textContent=`${currentRows.length} ZIPs · ${D.metros[S.city].label} · ${D.quarters[S.q]} · ${themeName()} · ${fundingUnits()}`;$('saveCSV').href=exportUrl;$('saveCSV').download=`${S.city}-${D.quarters[S.q]}-lag-${A.lag}-${A.basis}.csv`;$('copyStatus').textContent='';$('exportDialog').showModal();};
  $('copyCSV').onclick=async()=>{try{await navigator.clipboard.writeText($('exportText').value);$('copyStatus').textContent='Copied.';}catch{$('exportText').focus();$('exportText').select();$('copyStatus').textContent='Text selected. Press your copy shortcut.';}};

  if($('effRadius')) $('effRadius').onchange = renderCapitalEfficiency;
  if($('effIncome')) $('effIncome').onchange = renderCapitalEfficiency;
  renderCapitalEfficiency();
  renderAnalysis();
}

function populationStats(city,zip=null,lag=A.lag,width=A.window){
  const all=GEO.features.filter(f=>f.properties.metro===city&&(!zip||f.properties.zip===zip));
  const covered=all.filter(f=>perResident(0,populationOf(f.properties.zip),A.populationMinimum)!=null);
  let population=0,funding=0,complete=covered.length>0,reviewSum=0,reviews=0;
  for(const f of covered){const z=f.properties.zip,a=zipView(z);population+=populationOf(z);const amount=fundingWindow(a.inv,S.q,lag,width);if(amount==null)complete=false;else funding+=amount;if(a.sent[S.q]!=null){reviewSum+=a.sent[S.q]*a.n[S.q];reviews+=a.n[S.q];}}
  return {population:covered.length?population:null,funding:complete?funding:null,rate:complete?perResident(funding,population):null,sent:reviews?reviewSum/reviews:null,covered:covered.length,total:all.length};
}
function renderPopulation(){
  $('populationMinimumValue').textContent=fmt.format(A.populationMinimum);$('populationMinimum').setAttribute('aria-valuetext',A.populationMinimum+' residents (2020)');
  $('fundingAxisNote').textContent=`Funding axis: signed log of ${A.basis==='resident'?'dollars per 2020 resident':'total net obligations'}. Equal dot size per ZIP. Click a dot to select it.`;
  const now=populationStats(S.city,S.zip,0,1);$('mapPopulationLabel').textContent=S.zip?'Population (2020)':'Population (covered ZCTAs, 2020)';$('mapPopulation').textContent=S.zip?(populationOf(S.zip)==null?'Unavailable':fmt.format(populationOf(S.zip))):(now.population==null?'Unavailable':fmt.format(now.population));$('mapResidentRate').textContent=residentMoney(now.rate);
  const s=populationStats(S.city,S.zip);$('populationScope').textContent=(S.zip?'ZIP '+S.zip:D.metros[S.city].label)+' · funding window follows lag controls';
  $('populationTotal').textContent=s.population==null?'Unavailable':fmt.format(s.population);$('populationFunding').textContent=s.funding==null?'Unavailable':money(s.funding);$('populationRate').textContent=residentMoney(s.rate);
  $('populationCoverage').textContent=`${s.covered} of ${s.total} mapped ZCTAs meet the ${fmt.format(A.populationMinimum)}-resident minimum.${S.zip&&populationOf(S.zip)!=null?' Selected ZIP population: '+fmt.format(populationOf(S.zip))+'.':''}`;
  $('populationRows').innerHTML=Object.entries(D.metros).map(([city,m])=>{const r=populationStats(city);return `<tr data-selected="${city===S.city}"><td><button data-pop-city="${city}">${m.label}</button></td><td>${r.population==null?'Unavailable':fmt.format(r.population)}</td><td>${r.funding==null?'Unavailable':money(r.funding)}</td><td>${residentMoney(r.rate)}</td><td>${score(r.sent)}</td><td>${r.covered} / ${r.total}</td></tr>`;}).join('');
  if(A.basis==='resident')$('windowAmount').textContent=s.rate==null?'Per-resident window unavailable':residentMoney(s.rate)+' per 2020 resident · '+(S.zip?'selected ZIP':'covered mapped areas');
}
