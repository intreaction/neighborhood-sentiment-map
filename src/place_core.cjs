// Shared, deterministic proposal tools. Conversation never supplies model outputs.
const {projectEstimate} = require('./project_model_math.js');
const TYPES = ['Civic park', 'Greenway / public space', 'Civic plaza / transit access', 'Streetcar / transit', 'Streetscape / public space'];
const ALLOWED = new Set(['city', 'project_id', 'longitude', 'latitude', 'project_type', 'cost_millions']);
function distanceMeters(a, b) {
  const rad = Math.PI / 180;
  const dlat = (b[1] - a[1]) * rad, dlon = (b[0] - a[0]) * rad;
  const v = Math.sin(dlat / 2) ** 2 + Math.cos(a[1] * rad) * Math.cos(b[1] * rad) * Math.sin(dlon / 2) ** 2;
  return 6371008.8 * 2 * Math.atan2(Math.sqrt(v), Math.sqrt(Math.max(0, 1 - v)));
}
function inBounds(point, bounds) {
  return bounds && point[0] >= bounds[0] && point[0] <= bounds[2] && point[1] >= bounds[1] && point[1] <= bounds[3];
}
function placeProfile(data, state) {
  const city = data.cities.find(c => c.id === state.city);
  const point = [state.longitude, state.latitude];
  if (!city || !point.every(Number.isFinite) || !inBounds(point, city.bounds)) {
    return {status:'outside_coverage', inventoried_businesses:null, baseline_reviewed:null,
      pre_reviews_per_business:null, reviews:null, radius_meters:500, baseline_years:data.baseline_years};
  }
  const near = city.businesses.filter(b => distanceMeters(point, b) <= 500);
  const reviewed = near.filter(b => b[2] > 0);
  const reviews = reviewed.reduce((sum, b) => sum + b[2], 0);
  return {status: reviewed.length ? 'available' : 'no_reviews', inventoried_businesses:near.length,
    baseline_reviewed:reviewed.length, pre_reviews_per_business:reviewed.length ? reviews/reviewed.length : null,
    reviews, radius_meters:500, baseline_years:data.baseline_years};
}
function normalizeType(value, data) {
  const types = [...new Set([...(data.projects || []).map(p=>p.project_type), ...TYPES])];
  const exact = types.find(t=>t.toLowerCase()===value.toLowerCase());
  if (exact) return exact;
  if (/greenway|trail/i.test(value)) return types.find(t=>/greenway/i.test(t)) || TYPES[1];
  if (/streetcar|transit|rail/i.test(value)) return types.find(t=>/streetcar/i.test(t)) || TYPES[3];
  if (/streetscape|sidewalk/i.test(value)) return TYPES[4];
  if (/plaza|square/i.test(value)) return types.find(t=>/plaza/i.test(t)) || TYPES[2];
  if (/park|public space/i.test(value)) return TYPES[0];
  throw new Error('Choose a park, plaza, greenway, streetscape, or transit project.');
}
function updateProposal(state, changes, data) {
  if (!changes || typeof changes !== 'object' || Array.isArray(changes)) throw new Error('Proposal changes must be an object.');
  for (const k of Object.keys(changes)) if (!ALLOWED.has(k)) throw new Error('Unknown proposal field: '+k);
  const next = {...state};
  if (changes.city !== undefined) {
    if (typeof changes.city !== 'string') throw new Error('Choose a covered city.');
    const city = data.cities.find(c=>[c.id,c.label].some(s=>s.toLowerCase()===changes.city.toLowerCase()));
    if (!city) throw new Error('That city is outside the five-city map coverage.');
    next.city=city.id; [next.longitude,next.latitude]=city.center; next.project_id=null;
    if (placeProfile(data,next).status !== 'available') {
      const nearby = city.businesses.filter(b=>b[2]>0 && inBounds(b,city.bounds))
        .sort((a,b)=>distanceMeters(city.center,a)-distanceMeters(city.center,b))[0];
      if (nearby) [next.longitude,next.latitude]=nearby;
    }
  }
  if (changes.project_id !== undefined) {
    const project=data.projects.find(p=>p.id===changes.project_id);
    if (!project || !data.cities.some(c=>c.id===project.city_id)) throw new Error('That project is outside the five-city map coverage. It remains available in the evidence library.');
    next.city=project.city_id; [next.longitude,next.latitude]=project.center; next.project_id=project.id;
  }
  if ((changes.longitude === undefined) !== (changes.latitude === undefined)) throw new Error('Provide both longitude and latitude.');
  if (changes.longitude !== undefined) {
    if (!Number.isFinite(changes.longitude)||!Number.isFinite(changes.latitude)||Math.abs(changes.longitude)>180||Math.abs(changes.latitude)>90) throw new Error('Enter valid longitude and latitude.');
    next.longitude=changes.longitude; next.latitude=changes.latitude; next.project_id=null;
  }
  if (changes.cost_millions !== undefined) {
    if (!Number.isFinite(changes.cost_millions)||changes.cost_millions<=0||changes.cost_millions>1000000) throw new Error('Budget must be a positive number in millions of dollars.');
    next.cost_millions=changes.cost_millions;
  }
  if (changes.project_type !== undefined) {
    if (typeof changes.project_type !== 'string') throw new Error('Choose a project type.');
    next.project_type=normalizeType(changes.project_type,data);
  }
  const profile = placeProfile(data,next);
  if (profile.status === 'outside_coverage') throw new Error('Choose a location inside the mapped business-data coverage.');
  if (profile.status !== 'available') throw new Error('Placement requires a business with 2018–2019 reviews within 500 m. Choose a point near the business dots.');
  return next;
}
function inspectProposal(state,data,model) {
  const profile=placeProfile(data,state);
  const inputs={cost_millions:state.cost_millions,project_type:state.project_type,
    baseline_reviewed:profile.baseline_reviewed,pre_reviews_per_business:profile.pre_reviews_per_business};
  const result=projectEstimate(model,inputs);
  if(profile.status==='outside_coverage') result.errors.coverage='This point is outside the available geographic coverage.';
  return {proposal:{...state},profile,inputs,result,model_version:model.version,
    target:model.target, interpretation:'Retrospective scenario using a 2018–2019 Yelp baseline from the January 2022 archive. A two-post-year activity proxy, not annual activity, financial ROI, or a causal budget effect. Point-radius catchments may differ from historical project footprints. Project type changes comparables, not the fitted estimate.'};
}
// Offline command mode intentionally supports a bounded grammar; it is not an AI chat model.
function parseCommand(text,data) {
  const value=text.trim(); if(!value) throw new Error('Type a proposal or question.');
  const lower=value.toLowerCase(); const changes={};
  if (/-\s*\$?\s*\d+(?:\.\d+)?\s*(million|billion|thousand|m\b|k\b|b\b)/i.test(value) || /-\s*\$|\$\s*-/.test(value)) throw new Error('Budget must be positive.');
  if (/\b(reset|start over)\b/.test(lower)) return {action:'reset'};
  const project=data.projects.slice().sort((a,b)=>b.name.length-a.name.length).find(p=>lower.includes(p.name.toLowerCase())||lower.includes(p.id.replace(/-/g,' ')));
  if(project) changes.project_id=project.id;
  else { const city=data.cities.find(c=>lower.includes(c.label.toLowerCase())||lower.includes(c.id.toLowerCase())); if(city) changes.city=city.id; }
  const coordinate=value.replace(/\$\s*[\d,]+(?:\.\d+)?/g,'').match(/(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)/);
  if(coordinate) {changes.longitude=Number(coordinate[1]);changes.latitude=Number(coordinate[2]);}
  const amount=value.match(/\$\s*([\d,]+(?:\.\d+)?)\s*(million|billion|thousand|m\b|k\b|b\b)?/i) || value.match(/\b(\d+(?:\.\d+)?)\s*(million|billion|thousand)\b/i) || value.match(/\b(?:budget|cost|spend)\s*(?:of|is|to|at|=)?\s*(\d+(?:\.\d+)?)\s*(m|k|b)\b/i);
  if(amount) {
    const raw=Number(amount[1].replace(/,/g,'')); const unit=(amount[2]||'dollars').toLowerCase();
    changes.cost_millions=raw*({million:1,m:1,billion:1000,b:1000,thousand:.001,k:.001,dollars:.000001}[unit]);
  }
  const type=lower.match(/\b(greenway|trail|streetcar|transit|streetscape|sidewalk|plaza|square|park)\b/);
  if(type && (!project || /\b(build|make|propose|instead|project type)\b/.test(lower))) changes.project_type=normalizeType(type[1],data);
  // A named project selects a location, not its historical cost or outcome.
  if(Object.keys(changes).length) return {action:'update',changes};
  if(/\b(why|model|uncertain|uncertainty|risk|reliable|confidence|limitation|accuracy)\b/.test(lower)) return {action:'explain'};
  if(/\b(business|businesses|nearby|estimate|efficiency|review|reviews|how many|what is|what's|summary)\b/.test(lower)) return {action:'inspect'};
  throw new Error('Command mode understands places, project types and budgets. Try “Show Dilworth Park”, “Build a plaza here for $25 million”, or “How many businesses are nearby?”');
}
module.exports={TYPES,distanceMeters,inBounds,placeProfile,normalizeType,updateProposal,inspectProposal,parseCommand};
