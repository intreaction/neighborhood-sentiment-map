#!/usr/bin/env node
// One local HTTP request per presentation action. No browser automation.
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
export async function bridgeRequest(path,{method='GET',body,runtimeFile=new URL('../.place-runtime.json',import.meta.url)}={}){
  let runtime;try{runtime=JSON.parse(await readFile(runtimeFile,'utf8'));}catch{throw new Error('Place Lab is not running. Start it with npm run start:place.');}
  const response=await fetch(runtime.url+path,{method,headers:{Authorization:`Bearer ${runtime.token}`,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:AbortSignal.timeout(10000)});
  const result=await response.json();if(!response.ok)throw Object.assign(new Error(result.error),{result});return result;
}
function parse(argv){
  const tool=argv.shift();if(!tool||tool==='--help')return null;
  const args={},options={};
  if(argv[0]?.startsWith('{'))Object.assign(args,JSON.parse(argv.shift()));
  while(argv.length){
    const flag=argv.shift();if(!flag.startsWith('--'))throw new Error(`Unexpected argument ${flag}.`);
    const key=flag.slice(2).replaceAll('-','_');
    let value;if(['show','reset'].includes(key)&&(!argv[0]||argv[0].startsWith('--')))value=true;else{value=argv.shift();if(value===undefined)throw new Error(`${flag} needs a value.`);}
    if(key==='args'){Object.assign(args,JSON.parse(value));continue;}
    if(['session','command_id'].includes(key)){options[key==='session'?'session_id':key]=value;continue;}
    if(['limit','steps','smooth','length'].includes(key))value=Number(value);
    else if(['show','reset'].includes(key)&&typeof value==='string')value=value==='true'?true:value==='false'?false:value;
    else if(['time','filters'].includes(key))value=JSON.parse(value);
    else if(key==='zips')value=value.split(',');
    args[key]=value;
  }
  return {tool,arguments:args,...options};
}
async function main(){
  const payload=parse(process.argv.slice(2));
  if(!payload){console.log(`Place Lab voice CLI\n\nnode src/place_cli.mjs get_context\nnode src/place_cli.mjs set_view --city Tucson\nnode src/place_cli.mjs rank_areas --measure engagement --limit 1 --show\nnode src/place_cli.mjs navigate --direction down\nnode src/place_cli.mjs get_area_profile --zip 85701\nnode src/place_cli.mjs tools\nnode src/place_cli.mjs sessions\n\nUse --session ID when several pages are connected.\nUse --args '{"time":{"period":"2016Q3"}}' for nested arguments.\nResponses are JSON; say is the short spoken answer.`);return;}
  const result=payload.tool==='tools'?await bridgeRequest('/api/tools'):payload.tool==='sessions'?await bridgeRequest('/api/sessions'):await bridgeRequest('/api/call',{method:'POST',body:payload});
  console.log(JSON.stringify(result));
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)main().catch(error=>{console.log(JSON.stringify(error.result??{ok:false,error:error.message}));process.exitCode=1;});
