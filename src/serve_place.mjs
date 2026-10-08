#!/usr/bin/env node
// Local static site + in-memory query engine + acknowledged SSE command broker.
import http from 'node:http';
import {readFile,writeFile,unlink} from 'node:fs/promises';
import {randomBytes,randomUUID,timingSafeEqual,createHash} from 'node:crypto';
import {resolve,extname,sep} from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';
import {createPlaceService,BridgeError,validate} from './place_service.mjs';

const root=resolve(fileURLToPath(new URL('..',import.meta.url))),web=resolve(root,'web');
export const runtimePath=resolve(root,'.place-runtime.json');
const TYPES={'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.mjs':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json','.svg':'image/svg+xml','.png':'image/png','.jpg':'image/jpeg','.jpeg':'image/jpeg','.woff2':'font/woff2'};
const equal=(a,b)=>{const x=Buffer.from(a??''),y=Buffer.from(b??'');return x.length===y.length&&timingSafeEqual(x,y);};
export function createBridgeServer({commandTimeoutMs=5000}={}){
  const service=createPlaceService(import.meta.url),token=randomBytes(32).toString('hex'),sessions=new Map(),requests=new Map();
  const json=(res,status,value)=>{const raw=JSON.stringify(value);res.writeHead(status,{'Content-Type':'application/json','Content-Length':Buffer.byteLength(raw)});res.end(raw);};
  async function body(req){
    let text='',bytes=0;
    for await(const chunk of req){bytes+=chunk.length;if(bytes>65536)throw new BridgeError('Request body exceeds 64 KiB.','body_too_large',413);text+=chunk;}
    try{return JSON.parse(text);}catch{throw new BridgeError('Request body must be JSON.');}
  }
  const connected=()=>[...sessions.values()].filter(s=>s.stream&&!s.stream.destroyed);
  function target(id,required){
    if(id){const s=sessions.get(id);if(!s?.stream)throw new BridgeError('That presentation page is disconnected.','page_unavailable',409);return s;}
    const candidates=connected();
    if(candidates.length>1)throw new BridgeError('Multiple pages are connected. Specify session_id from /api/sessions.','ambiguous_session',409);
    if(candidates.length===1)return candidates[0];
    if(required)throw new BridgeError('Open Place Lab from this server before sending view commands.','page_unavailable',409);
    return null;
  }
  const queue=(session,fn)=>{const promise=(session.queue??Promise.resolve()).catch(()=>{}).then(fn);session.queue=promise;return promise;};
  async function deliver(session,actions,commandId){
    if(!session.stream||session.stream.destroyed)throw new BridgeError('Presentation page disconnected.','page_unavailable',409);
    const id=randomUUID(),expected=session.revision;
    return new Promise((resolve_,reject)=>{
      const timer=setTimeout(()=>{session.pending.delete(id);reject(new BridgeError('The page did not acknowledge the command in time. Inspect the page before retrying.','command_timeout',504));},commandTimeoutMs);
      session.pending.set(id,{resolve:resolve_,reject,timer});
      session.stream.write(`event: command\ndata: ${JSON.stringify({id,command_id:commandId,expected_revision:expected,actions,expires_at:Date.now()+commandTimeoutMs})}\n\n`);
    });
  }
  async function call(payload){
    validate({type:'object',properties:{tool:{type:'string'},arguments:{type:'object'},session_id:{type:'string'},command_id:{type:'string'}},required:['tool'],additionalProperties:false},payload);
    const commandId=payload.command_id??randomUUID(),signature=createHash('sha256').update(JSON.stringify({tool:payload.tool,arguments:payload.arguments??{},session_id:payload.session_id})).digest('hex');
    if(requests.has(commandId)){const previous=requests.get(commandId);if(previous.signature!==signature)throw new BridgeError('command_id was already used with different arguments.','command_conflict',409);return previous.promise;}
    const promise=(async()=>{
      const start=performance.now(),args=payload.arguments??{};
      const needsPage=['set_view','set_time','navigate'].includes(payload.tool);
      const session=target(payload.session_id,needsPage||args.show===true);
      const execute=async()=>{
        const inputRevision=session?.revision??null,snapshot=session?.view??null;
        if(session&&!snapshot)throw new BridgeError('The page is connecting; retry once its state is ready.','page_not_ready',409);
        const planned=await service.plan(payload.tool,args,snapshot);
        let applied=null;
        if(planned.actions.length){
          applied=await deliver(session,planned.actions,commandId);
          if(!applied.ok)throw new BridgeError(applied.error??'Page rejected command.',applied.code??'page_error',409);
          if(!planned.queryOnly)planned.result={...applied.result,ok:true};
        }
        return {...planned.result,command_id:commandId,context:{...planned.context,session_id:session?.id??null,input_revision:inputRevision},display:applied?{status:'applied',view:applied.view,revision:session.revision}:null,timing:{server_ms:Math.round((performance.now()-start)*100)/100}};
      };
      return session?queue(session,execute):execute();
    })();
    requests.set(commandId,{signature,promise,created:Date.now()});
    // Failures are cached too: reusing an ID never repeats a possibly applied action.
    return promise;
  }
  function validateView(view){
    if(!view||typeof view!=='object'||!['Philadelphia','TampaBay','Nashville','NewOrleans','Tucson'].includes(view.city))throw new BridgeError('Invalid page city.');
    const t=view.time?.setting;
    if(t)validate({type:'object',properties:{mode:{type:'string',enum:['snapshot','compare']},grain:{type:'string',enum:['quarter','month']},smooth:{type:'integer',enum:[1,3,12]},at:{type:'integer',minimum:0,maximum:119},from:{type:'integer',minimum:0,maximum:119},to:{type:'integer',minimum:0,maximum:119},length:{type:'integer',minimum:1,maximum:60}},required:['mode','grain','smooth','at','from','to','length'],additionalProperties:false},t);
  }
  const server=http.createServer(async(req,res)=>{
    res.setHeader('X-Content-Type-Options','nosniff');res.setHeader('Cache-Control','no-store');res.setHeader('Referrer-Policy','no-referrer');res.setHeader('Cross-Origin-Resource-Policy','same-origin');
    try{
      const port=server.address().port,host=req.headers.host,origin=req.headers.origin;
      if(!['127.0.0.1','::ffff:127.0.0.1'].includes(req.socket.remoteAddress)||![`127.0.0.1:${port}`,`localhost:${port}`].includes(host)||origin&&origin!==`http://${host}`)throw new BridgeError('Use the loopback origin serving Place Lab.','forbidden',403);
      const path=new URL(req.url,`http://${host}`).pathname;
      if(path==='/api/connect'&&req.method==='POST'){
        if(origin!==`http://${host}`)throw new BridgeError('Browser registration requires the page origin.','forbidden',403);
        const input=await body(req);let session=sessions.get(input.session_id);
        if(!session||session.stream&&!session.stream.destroyed){session={id:randomUUID(),revision:0,view:null,stream:null,pending:new Map(),updated:Date.now(),queue:Promise.resolve()};sessions.set(session.id,session);}
        res.setHeader('Set-Cookie',`place_bridge=${token}; HttpOnly; SameSite=Strict; Path=/api`);
        json(res,200,{session_id:session.id,revision:session.revision,dataset_revision:service.revision});return;
      }
      if(path.startsWith('/api/')){
        const cookie=req.headers.cookie?.split(';').map(s=>s.trim()).find(s=>s.startsWith('place_bridge='))?.slice(13);
        const bearer=req.headers.authorization?.replace(/^Bearer /,'');
        if(!equal(bearer??cookie,token))throw new BridgeError('Local bridge credentials required. Use place_cli.mjs.','unauthorized',401);
        if(path==='/api/health'&&req.method==='GET'){json(res,200,{ok:true,dataset_revision:service.revision});return;}
        if(path==='/api/tools'&&req.method==='GET'){json(res,200,{tools:service.definitions,dataset_revision:service.revision});return;}
        if(path==='/api/sessions'&&req.method==='GET'){json(res,200,{sessions:connected().map(s=>({session_id:s.id,revision:s.revision,view:s.view,updated_at:s.updated}))});return;}
        if(path==='/api/call'&&req.method==='POST'){json(res,200,await call(await body(req)));return;}
        const match=path.match(/^\/api\/sessions\/([^/]+)\/(events|state|results)$/),session=match&&sessions.get(match[1]);
        if(!session)throw new BridgeError('Unknown endpoint or session.','not_found',404);
        if(match[2]==='events'&&req.method==='GET'){
          session.stream?.end();session.stream=res;session.updated=Date.now();
          res.writeHead(200,{'Content-Type':'text/event-stream','Connection':'keep-alive','X-Accel-Buffering':'no'});res.write('retry: 500\n: connected\n\n');
          const heartbeat=setInterval(()=>res.write(': heartbeat\n\n'),10000);
          res.on('close',()=>{clearInterval(heartbeat);if(session.stream===res){session.stream=null;for(const p of session.pending.values()){clearTimeout(p.timer);p.reject(new BridgeError('Page disconnected during command.','page_disconnected',409));}session.pending.clear();}});return;
        }
        if(match[2]==='state'&&req.method==='POST'){
          const input=await body(req);validateView(input.view);
          if(!Number.isInteger(input.revision)||input.revision<session.revision)throw new BridgeError('Outdated page state.','state_conflict',409);
          session.view=input.view;session.revision=input.revision;session.updated=Date.now();json(res,200,{ok:true,revision:session.revision});return;
        }
        if(match[2]==='results'&&req.method==='POST'){
          const input=await body(req),pending=session.pending.get(input.id);
          if(pending){
            if(input.view){validateView(input.view);if(Number.isInteger(input.revision)&&input.revision>=session.revision){session.view=input.view;session.revision=input.revision;}}
            session.pending.delete(input.id);clearTimeout(pending.timer);pending.resolve(input);
          }
          json(res,200,{ok:true});return;
        }
        throw new BridgeError('Unsupported method.','method_not_allowed',405);
      }
      if(!['GET','HEAD'].includes(req.method))throw new BridgeError('Unsupported method.','method_not_allowed',405);
      const decoded=decodeURIComponent(path),parts=decoded.split('/');
      if(parts.some(p=>p.startsWith('.')))throw new BridgeError('Not found.','not_found',404);
      const file=resolve(web,'.'+(decoded==='/'?'/index.html':decoded));if(!file.startsWith(web+sep))throw new BridgeError('Not found.','not_found',404);
      const raw=service.assets.get(file.slice(web.length+1))??await readFile(file);
      res.writeHead(200,{'Content-Type':TYPES[extname(file)]??'application/octet-stream','Content-Length':raw.length});res.end(req.method==='HEAD'?undefined:raw);
    }catch(error){
      if(res.headersSent){res.destroy();return;}
      const status=error.status??(error.code==='ENOENT'||error.code==='EISDIR'?404:500);
      json(res,status,{ok:false,error:status===500?'Local bridge error. See the server terminal.':error.message,code:error instanceof BridgeError?error.code:status===404?'not_found':'server_error'});
      if(status===500)console.error(error);
    }
  });
  const cleanup=setInterval(()=>{for(const [id,r] of requests)if(Date.now()-r.created>1800000)requests.delete(id);for(const [id,s] of sessions)if(!s.stream&&Date.now()-s.updated>1800000)sessions.delete(id);},60000);cleanup.unref();
  server.on('close',()=>clearInterval(cleanup));
  return {server,token,service,sessions};
}
async function main(){
  const args=process.argv.slice(2),portIndex=args.indexOf('--port'),port=portIndex>=0?Number(args[portIndex+1]):8766;
  if(!Number.isInteger(port)||port<0||port>65535)throw new Error('--port must be between 0 and 65535.');
  const bridge=createBridgeServer();
  try{
    const existing=JSON.parse(await readFile(runtimePath,'utf8'));
    const health=await fetch(`${existing.url}/api/health`,{headers:{Authorization:`Bearer ${existing.token}`},signal:AbortSignal.timeout(500)}).then(r=>r.json());
    if(health.ok&&health.dataset_revision===bridge.service.revision&&portIndex<0){console.log(`Place Lab already running: ${existing.url}/place.html`);if(args.includes('--open'))spawn('open',[`${existing.url}/place.html`],{stdio:'ignore'});bridge.server.close();return;}
  }catch{}
  await new Promise((resolve_,reject)=>{bridge.server.once('error',error=>{if(error.code==='EADDRINUSE')bridge.server.listen(0,'127.0.0.1',resolve_);else reject(error);});bridge.server.listen(port,'127.0.0.1',resolve_);});
  const url=`http://127.0.0.1:${bridge.server.address().port}`;
  await writeFile(runtimePath,JSON.stringify({url,token:bridge.token,pid:process.pid,dataset_revision:bridge.service.revision})+'\n',{mode:0o600});
  console.log(`Place Lab: ${url}/place.html\nVoice CLI: node src/place_cli.mjs get_context`);
  if(args.includes('--open'))spawn('open',[`${url}/place.html`],{stdio:'ignore'});
  const shutdown=async()=>{try{const r=JSON.parse(await readFile(runtimePath,'utf8'));if(r.token===bridge.token)await unlink(runtimePath);}catch{}for(const s of bridge.sessions.values())s.stream?.end();bridge.server.close(()=>process.exit(0));};
  process.on('SIGINT',shutdown);process.on('SIGTERM',shutdown);
}
if(process.argv[1]&&import.meta.url===pathToFileURL(resolve(process.argv[1])).href)main().catch(error=>{console.error(error.message);process.exitCode=1;});
