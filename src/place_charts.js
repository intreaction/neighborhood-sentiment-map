import insights from './place_insights.cjs';
import {mountLineChart,mountBarChart,mountValidationChart,clearChart} from './place_chart_components.tsx';
const $=id=>document.getElementById(id);
const n=(value,digits=0)=>Number.isFinite(value)?value.toLocaleString('en-US',{maximumFractionDigits:digits}):'—';
const esc=text=>String(text).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const green='#245c49',orange='#b56b32',gray='#889686';
function table(headers,rows) {
  return `<details class="chart-data"><summary>View chart data</summary><div class="chart-table-wrap"><table><thead><tr>${headers.map(h=>`<th scope="col">${esc(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(v=>`<td>${esc(v)}</td>`).join('')}</tr>`).join('')}</tbody></table></div></details>`;
}
function lineChart(id,options) {
  const {series,xLabel,xFormat=v=>n(v),yFormat=v=>n(v)}=options;
  const rows=[...new Set(series.flatMap(s=>s.points.map(p=>p.x)))].sort((a,b)=>a-b).map(x=>[xFormat(x),...series.map(s=>{const p=s.points.find(p=>p.x===x);return p&&Number.isFinite(p.y)?yFormat(p.y):'Unavailable';})]);
  mountLineChart(id,{...options,xFormat,yFormat},table([xLabel,...series.map(s=>s.label)],rows));
}
function contributions(id,info,ce) {
  const labels={pre_reviews_per_business:'Review intensity',cost_millions:'Budget',baseline_reviewed:'Reviewed businesses'};
  const rows=[{label:'Model intercept',value:info.intercept},...info.contributions.map(r=>({label:labels[r.name]||r.name,value:r.value})),{label:'Resulting score',value:ce}];
  mountBarChart(id,{title:'Regression contributions to the score',rows,unit:'Excess reviews / $1M'},table(['Term','Reviews / $1M'],rows.map(r=>[r.label,n(r.value,2)])));
}
export function renderHistory(history,id) {
  const p=history.projects.find(p=>p.id===id),s=insights.historicalSeries(p);
  if(!s){clearChart('historyChart','This project has too few years of data to chart.');$('historyNote').textContent='';renderTopics(history,id);return;}
  const series=[{label:'Nearby businesses',color:green,points:s.near.points},{label:'Comparison area',color:gray,points:s.far.points}];
  const pre=s.near.points.filter(p=>p.period!=='post');
  if(s.near.fit)series.push({label:`Nearby pre-opening OLS fit (${s.near.fit.n} years)`,color:orange,dashed:true,points:[pre[0].x,pre.at(-1).x].map(x=>({x,y:s.near.fit.intercept+s.near.fit.slope*x}))});
  const opening=Number(s.opening.slice(0,4))+(Number(s.opening.slice(5,7))-1)/12;
  lineChart('historyChart',{title:`${s.project}: observed annual business engagement`,series,xLabel:'Calendar year',yLabel:'Review index · pre-opening annual average = 100',xFormat:v=>String(Math.round(v)),opening});
  renderTopics(history,id);
  $('historyNote').textContent=`${s.project}, opened ${s.opening}. Each area is indexed to its own pre-opening annual average. These use the project's own footprint and comparison area. Missing years are not zero, and opening or construction years may be left out. The dashed line fits only the years before opening. It is not a prediction.`;
}
export function renderInsights(snapshot,model,history) {
  const info=insights.scenarioInsights(snapshot,model);
  if(!info) {
    $('engagementMetrics').innerHTML='<p class="insight-empty">The model cannot estimate engagement for this combination of inputs. Historical examples remain available below.</p>';
    for(const id of ['timelineChart','budgetChart','contributionChart'])clearChart(id,'Estimate withheld. Select a supported location and budget.');
    $('timelineNote').textContent='No timing illustration is shown without a supported two-year estimate.';
  } else {
    const cards=[['Estimated excess reviews',n(info.total),'Across the two-post-year analysis window'],['Relative to baseline volume',n(info.baselineShare,1)+'%','Two-year excess ÷ 2018–2019 reviews; not a forecast growth rate'],['Average per reviewed business',n(info.perBusiness,1),'Arithmetic average; individual business effects are unknown'],['Historical error envelope',`${n(info.error.low)} to ${n(info.error.high)}`,'Excess reviews at two years; not a confidence interval']];
    $('engagementMetrics').innerHTML=cards.map(([label,value,note])=>`<div><p class="eyebrow">${esc(label)}</p><strong>${esc(value)}</strong><p>${esc(note)}</p></div>`).join('');
    lineChart('timelineChart',{title:'Assumed even accumulation across the two-post-year analysis window',series:[{label:'Even-spread illustration',color:green,points:info.timeline}],xLabel:'Months into the two-post-year window',yLabel:'Cumulative excess reviews',endpoint:{x:24,...info.error}});
    $('timelineNote').textContent=`Two-year model total: ${n(info.total)} excess reviews. Six- and twelve-month values are arithmetic allocations, not fitted forecasts. Historical outcomes use the first two full calendar years after opening, excluding the opening year. The error envelope is shown only at the two-post-year model horizon.`;
    lineChart('budgetChart',{title:'Budget sensitivity within historical model support',series:[{label:'Fitted two-year excess reviews',color:green,points:info.sensitivity},{label:'Your proposal',color:orange,points:[{x:snapshot.proposal.cost_millions,y:info.total}]}],xLabel:'Budget · $ million',yLabel:'Estimated two-year excess reviews'});
    contributions('contributionChart',info,snapshot.result.estimate.ce);
  }
  const candidate=model.candidates[model.selected_model];
  $('validationNote').textContent=`Validation: ${candidate.city_metrics.n} historical projects; city-held-out mean absolute error ${n(candidate.city_metrics.mae,1)} reviews per $1M. Direction was correct for ${n(candidate.city_metrics.sign_accuracy*100)}% of cases. The model’s advantage over a mean-only comparison is not robust to all timing exclusions.`;
  renderDecisionContext(snapshot,model,info);
  renderValidation(model);
  renderHistory(history,$('historyProject').value);
}

export function renderTopics(history,id) {
  if(!$('topicChart'))return;
  const project=history.projects.find(p=>p.id===id),mode=$('topicMeasure').value;
  const labels={walking_accessibility:'Walking / accessibility',transit:'Transit',parking:'Parking',safety:'Safety',cleanliness_maintenance:'Cleanliness / maintenance',public_space:'Public space',construction:'Construction',food_service_value:'Food / service / value',neighborhood:'Neighborhood'};
  const records=insights.historicalTopics(project,mode);
  if(!records.length){clearChart('topicChart','Topic data are unavailable for this historical example.');$('topicNote').textContent='';return;}
  const rows=records.map(r=>({...r,color:mode==='complaints'?(r.value>0?orange:green):undefined,label:labels[r.topic]||r.topic,detail:`Nearby: ${n(r.nearPre,1)}% → ${n(r.nearPost,1)}%. Comparison change: ${n(r.farChange,1)} pp. ${r.sparse?'Sparse nearby topic counts; interpret cautiously.':''}`}));
  mountBarChart('topicChart',{title:`${project.project}: observed ${mode==='complaints'?'complaint':'topic discussion'} changes`,rows,unit:'Comparison-adjusted change · percentage points'},table(['Topic','Nearby pre %','Nearby post %','Comparison change · pp','Adjusted change · pp','Nearby pre / post topic reviews'],rows.map(r=>[r.label,n(r.nearPre,2),n(r.nearPost,2),n(r.farChange,2),n(r.value,2),`${r.preCount} / ${r.postCount}${r.sparse?' · sparse':''}`])));
  $('topicNote').textContent=`${project.project}: (nearby post − pre share) − (comparison post − pre share). ${mode==='complaints'?'Negative values mean a relative reduction in negative area experiences; positive values mean more complaints.':'Positive values mean more discussion, which may include praise or complaints.'} Topics overlap and do not sum to 100%. Rule-based labels are provisional, with no independent accuracy estimate. ${rows.filter(r=>r.sparse).length} topics have fewer than 20 nearby mentions in at least one period. These are historical observations, not validated forecasts or causal effects.`;
}
function renderValidation(model) {
  const candidate=model.candidates[model.selected_model];
  const rows=candidate.held_out.map(r=>({project:r.project,observed:r.observed_ce,predicted:r.city_prediction}));
  mountValidationChart('validationChart',rows,table(['Project','Observed reviews / $1M','City-held-out prediction','Absolute error'],rows.map(r=>[r.project,n(r.observed,1),n(r.predicted,1),n(Math.abs(r.observed-r.predicted),1)])));
  $('reliabilityNote').textContent=`Across ${candidate.city_metrics.n} projects, city-held-out mean absolute error is ${n(candidate.city_metrics.mae,1)} reviews per $1M, compared with ${n(model.mean_baseline.city_metrics.mae,1)} for the mean-only baseline. Direction was correct in ${n(candidate.city_metrics.sign_accuracy*100)}% of cases. Timing exclusions weaken this advantage; the chart does not establish causal impact.`;
}
function renderDecisionContext(snapshot,model,info) {
  const {profile,result,proposal}=snapshot;
  const totalInventory=profile.inventoried_businesses,coverage=totalInventory>0?profile.baseline_reviewed/totalInventory*100:null;
  const candidate=model.candidates[model.selected_model];
  const nearest=result.similarity?model.training_rows.map(row=>{
    const distance=Math.sqrt(candidate.feature_names.reduce((sum,field,i)=>{
      const transform=value=>model.feature_schema[field].transform==='log1p'?Math.log1p(value):value;
      const delta=(transform(snapshot.inputs[field])-transform(row.inputs[field]))/candidate.feature_scales[i];
      return sum+delta*delta;
    },0)/candidate.feature_names.length);
    return {...row,distance};
  }).sort((a,b)=>a.distance-b.distance)[0]:null;
  const rows=[['Data behind this location',`${n(profile.baseline_reviewed)} reviewed businesses from ${n(totalInventory)} listed businesses within 500 m (${n(coverage,1)}% with baseline reviews). This measures historical Yelp coverage, not the share of all local businesses.`],
    ['How to read the estimate',info?`${n(info.total)} estimated excess reviews over two post years at a $${n(proposal.cost_millions,1)}M budget. ${info.error.low<=0&&info.error.high>=0?'The historical error envelope spans zero, so the direction of change is uncertain.':'The historical error envelope stays on one side of zero, but is not a confidence interval.'}`:'The selected inputs are outside model support. No engagement estimate is available.'],
    ['Closest profile in the evidence',nearest?`${nearest.project} (${nearest.city}): observed ${n(nearest.observed_ce,1)} reviews / $1M; standardized profile distance ${n(nearest.distance,2)} versus support limit ${n(result.similarity?.threshold,2)}. Comparison ordering can prefer project type; this is the closest profile by distance.`:'No comparable profile is available for these inputs.'],
    ['What the evidence cannot decide','The model does not predict business revenue, visits, foot traffic, or public welfare. Project type does not change its fitted estimate. Topic charts describe historical examples; proposal-specific topic forecasts need additional local topic data and validation.']];
  $('decisionContext').innerHTML=rows.map(([title,body])=>`<div><h3>${esc(title)}</h3><p>${esc(body)}</p></div>`).join('');
}

export function decisionExport(snapshot,model,history,projectId,topicMode) {
  return {scenario:insights.scenarioInsights(snapshot,model),
    timing_assumption:'Even allocation across two full post-opening calendar years; intermediate months are not fitted forecasts.',
    historical_example:projectId,historical_topic_measure:topicMode,
    historical_topic_changes:insights.historicalTopics(history.projects.find(p=>p.id===projectId),topicMode),
    topic_interpretation:'Observed comparison-adjusted changes in overlapping provisional review labels, not proposal forecasts or causal effects.',
    city_holdout_validation:model.candidates[model.selected_model].city_metrics,
    mean_only_validation:model.mean_baseline.city_metrics};
}
