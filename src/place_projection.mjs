// What changed around past projects, measured against each project's own comparison
// area (difference in differences). Eleven type labels have one project each, so labels
// are grouped into families. Results are descriptive: familySummary reports plain means
// and ranges; the pooled familyEstimate exists only for the leave-one-out check, which
// showed families do not predict a held-out project better than the all-project mean.
export const PRIOR_WEIGHT=2;
export const FAMILIES={
  trail:{label:'Trail / greenway',note:'Linear trails, greenways and boardwalks'},
  waterfront:{label:'Waterfront park',note:'Riverfront parks and promenades'},
  civic:{label:'Civic park / plaza',note:'Downtown plazas and civic parks'},
  transit:{label:'Transit line',note:'Streetcar or rail service'}
};
export const PROJECT_FAMILY={
  'lafitte':'trail','the-rail-park':'trail','indianapolis-cultural-trail':'trail','schuylkill-boardwalk':'trail',
  'riverfront-ascend':'waterfront','tampa-riverwalk':'waterfront','crescent-park':'waterfront','water-works-park':'waterfront',
  'dilworth-park':'civic','gateway-arch-park':'civic',
  'sun-link':'transit'
};
// zipField names the matching ZIP measure; null means the definitions differ, so only the change is shown.
export const OUTCOMES=[
  {key:'activity',term:'engagement',better:1,label:'Business engagement',unit:'% change',zipField:'annual_review_density',zipUnit:'reviews / km² / year'},
  {key:'sentiment',term:'sentiment',better:1,label:'Average review sentiment',unit:'VADER points',zipField:'late_sentiment',zipUnit:'VADER compound, −1 to +1'},
  {key:'access',term:'negative_access',better:-1,label:'Negative access & parking mentions',unit:'percentage points',zipField:null},
  {key:'realm',term:'negative_realm',better:-1,label:'Negative public-space mentions',unit:'percentage points',zipField:null}
];

const mean=values=>values.reduce((s,v)=>s+v,0)/values.length;

// One row per eligible project. Activity is a log ratio so it converts to a multiplier.
export function projectEffects(history,excludedIds=[]){
  const skip=new Set(excludedIds);
  return history.projects.filter(p=>PROJECT_FAMILY[p.id]&&!skip.has(p.id)).map(p=>{
    const {near,far}=p.periods;
    const diff=field=>(near.post[field]-near.pre[field])-(far.post[field]-far.pre[field]);
    return {id:p.id,project:p.project,opening:p.opening,family:PROJECT_FAMILY[p.id],effects:{
      activity:Math.log(near.post.n_reviews/near.pre.n_reviews)-Math.log(far.post.n_reviews/far.pre.n_reviews),
      sentiment:diff('mean_sentiment'),
      access:100*diff('access_friction_share'),
      realm:100*diff('public_realm_complaint_share')
    }};
  });
}

export function familyEstimate(rows,family,prior=PRIOR_WEIGHT){
  const members=rows.filter(r=>r.family===family),outcomes={};
  for(const {key} of OUTCOMES){
    const all=rows.map(r=>r.effects[key]),own=members.map(r=>r.effects[key]);
    const overall=mean(all),sum=own.reduce((s,v)=>s+v,0);
    outcomes[key]={pooled:(sum+prior*overall)/(own.length+prior),family_mean:own.length?sum/own.length:null,overall_mean:overall,
      min:own.length?Math.min(...own):null,max:own.length?Math.max(...own):null};
  }
  return {family,n:members.length,members,outcomes};
}

// Leave one project out: does its family estimate beat the plain all-project mean?
export function leaveOneOut(rows,prior=PRIOR_WEIGHT){
  const result={};
  for(const {key} of OUTCOMES){
    let familyError=0,overallError=0;
    for(const row of rows){
      const rest=rows.filter(r=>r!==row),truth=row.effects[key];
      familyError+=Math.abs(familyEstimate(rest,row.family,prior).outcomes[key].pooled-truth);
      overallError+=Math.abs(mean(rest.map(r=>r.effects[key]))-truth);
    }
    result[key]={family_mae:familyError/rows.length,overall_mae:overallError/rows.length,n:rows.length};
  }
  return result;
}

// Plain family (or 'all') average and range of observed changes; activity as % change.
export function familySummary(rows,family){
  const members=family==='all'?rows:rows.filter(r=>r.family===family);
  const asChange=(key,v)=>key==='activity'?100*(Math.exp(v)-1):v;
  const outcomes={};
  for(const {key} of OUTCOMES){
    const values=members.map(r=>r.effects[key]);
    outcomes[key]=values.length?{mean:asChange(key,mean(values)),min:asChange(key,Math.min(...values)),max:asChange(key,Math.max(...values)),
      better:values.filter(v=>v*OUTCOMES.find(o=>o.key===key).better>0).length}:null;
  }
  return {family,n:members.length,members,outcomes};
}
