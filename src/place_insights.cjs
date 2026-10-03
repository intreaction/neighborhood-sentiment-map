const {projectEstimate}=require('./project_model_math.js');
function linearFit(points) {
  if(points.length<3)return null;
  const mx=points.reduce((s,p)=>s+p.x,0)/points.length,my=points.reduce((s,p)=>s+p.y,0)/points.length;
  const xx=points.reduce((s,p)=>s+(p.x-mx)**2,0);if(!xx)return null;
  const slope=points.reduce((s,p)=>s+(p.x-mx)*(p.y-my),0)/xx;
  const intercept=my-slope*mx;
  return {slope,intercept,n:points.length};
}
function historicalSeries(project) {
  if(!project)return null;
  const series={};
  for(const group of ['near','far']) {
    const pre=project.periods[group]?.pre;
    const baseline=pre?.n_reviews/Object.keys(pre?.by_year||{}).length;
    if(!(baseline>0))return null;
    const points=[];
    for(const period of ['early','pre','post'])for(const [year,count] of Object.entries(project.periods[group]?.[period]?.by_year||{})) {
      if(Number.isFinite(count))points.push({x:Number(year),y:count/baseline*100,count,period});
    }
    points.sort((a,b)=>a.x-b.x);
    const fit=linearFit(points.filter(p=>p.period!=='post'));
    series[group]={points,fit};
  }
  return {project:project.project,opening:project.opening,...series};
}
function scenarioInsights(snapshot,model) {
  if(snapshot.result.status!=='ok')return null;
  const {proposal,profile,result,inputs}=snapshot,total=result.estimate.net_reviews;
  const timeline=[0,6,12,18,24].map(month=>({x:month,y:total*month/24}));
  const budgetSpec=model.feature_schema.cost_millions;
  const budgets=Array.from({length:61},(_,i)=>Math.exp(Math.log(budgetSpec.min)+(Math.log(budgetSpec.max)-Math.log(budgetSpec.min))*i/60));
  budgets.push(proposal.cost_millions);budgets.sort((a,b)=>a-b);
  const sensitivity=budgets.map(cost=>{const r=projectEstimate(model,{...inputs,cost_millions:cost});return {x:cost,y:r.status==='ok'?r.estimate.net_reviews:null};});
  const candidate=model.candidates[model.selected_model];
  const contributions=candidate.feature_names.map((name,i)=>{
    const raw=inputs[name],value=model.feature_schema[name].transform==='log1p'?Math.log1p(raw):raw;
    return {name,value:candidate.coefficients[i]*(value-candidate.feature_means[i])/candidate.feature_scales[i]};
  });
  return {total,timeline,sensitivity,contributions,intercept:candidate.intercept,
    perBusiness:total/profile.baseline_reviewed,
    baselineShare:profile.reviews>0?total/profile.reviews*100:null,
    error:{low:result.empirical_error.low*proposal.cost_millions,high:result.empirical_error.high*proposal.cost_millions}};
}
function historicalTopics(project,mode='discussion') {
  if(!project)return [];
  const field=mode==='complaints'?'negative_share':'share';
  const countField=mode==='complaints'?'negative_reviews':'n_reviews';
  const periods=[project.periods.near?.pre,project.periods.near?.post,project.periods.far?.pre,project.periods.far?.post];
  if(periods.some(p=>!p||!p.n_reviews))return [];
  return Object.keys(periods[0].topics||{}).filter(topic=>mode!=='complaints'||topic!=='food_service_value').flatMap(topic=>{
    const values=periods.map(p=>p.topics?.[topic]);
    if(values.some(v=>!v||!Number.isFinite(v[field])))return [];
    const [nearPre,nearPost,farPre,farPost]=values.map(v=>v[field]*100);
    const preCount=values[0][countField],postCount=values[1][countField];
    return [{topic,nearPre,nearPost,farChange:farPost-farPre,value:(nearPost-nearPre)-(farPost-farPre),preCount,postCount,sparse:preCount<20||postCount<20}];
  });
}
module.exports={linearFit,historicalSeries,scenarioInsights,historicalTopics};
