// Optional agent adapter. Human controls and the model work without this API.
function createPlaceTools({getCatalog, onTool}) {
  const empty = {type:'object',properties:{},additionalProperties:false};
  const wrap = fn => async (args={}) => {
    try { return JSON.parse(JSON.stringify(await fn(args))); }
    catch(error) { return {ok:false,error:error.message}; }
  };
  const noArgs = args => {
    if (!args || typeof args !== 'object' || Array.isArray(args) || Object.keys(args).length) throw new Error('This read-only tool accepts an empty object.');
  };
  return [
    {name:'inspect_place_catalog',title:'Read covered places and project types',
      description:'Read supported city IDs, known project locations, project types and source years. Choose a known location or user-supplied coordinates; never invent geocoding.',
      inputSchema:empty,annotations:{readOnlyHint:true},execute:wrap(args=>{noArgs(args);return {ok:true,...getCatalog()};})},
    {name:'inspect_proposal',title:'Read the current proposal and actual estimate',
      description:'Read the visible proposal, actual 500m business counts, model support, computed estimate and historical limitations. Does not change state.',
      inputSchema:empty,annotations:{readOnlyHint:true},execute:wrap(args=>{noArgs(args);return onTool('inspect_proposal',{});})},
    {name:'update_proposal',title:'Update the visible proposal',
      description:'Apply user-selected location, type and budget to this page, returning actual measured business counts and model results. Reversible local scenario only. Budget is in millions USD; type affects comparables only. Supply both coordinates together. No microphone, paid API, navigation or publication.',
      inputSchema:{type:'object',additionalProperties:false,properties:{city:{type:'string'},project_id:{type:'string'},longitude:{type:'number',minimum:-180,maximum:180},latitude:{type:'number',minimum:-90,maximum:90},project_type:{type:'string'},cost_millions:{type:'number',exclusiveMinimum:0,maximum:1000000}}},
      annotations:{readOnlyHint:false},execute:wrap(args=>onTool('update_proposal',args))}
  ];
}
async function registerPlaceTools(context, tools) {
  if (!context || typeof context.registerTool !== 'function') return false;
  for (const tool of tools) await context.registerTool(tool);
  return true;
}
module.exports={createPlaceTools,registerPlaceTools};
