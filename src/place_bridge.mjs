// Browser adapter: push only named app operations, report actual page context.
export function connectPlaceBridge({call,current,subscribe=()=>()=>{}}){
  const status={state:'connecting',session_id:null,error:null};
  if(!['127.0.0.1','localhost'].includes(location.hostname)){status.state='static';return status;}
  let stream,stopped=false,revision=0,signature='',session=null,retryTimer,reportTimer,executing=false;
  let posts=Promise.resolve(),commands=Promise.resolve();
  const completed=new Map();
  const storageGet=()=>{try{return sessionStorage.getItem('place-session');}catch{return null;}};
  const storageSet=id=>{try{sessionStorage.setItem('place-session',id);}catch{}};
  async function post(path,value){
    const r=await fetch(path,{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify(value)});
    if(!r.ok)throw new Error((await r.json()).error??`HTTP ${r.status}`);
    return r.json();
  }
  function capture(){const view=current(),text=JSON.stringify(view);if(text!==signature){signature=text;revision++;}return {view,revision};}
  function report(){
    capture();clearTimeout(reportTimer);
    if(!session||executing)return;
    reportTimer=setTimeout(()=>{const state=capture();posts=posts.catch(()=>{}).then(()=>post(`/api/sessions/${session}/state`,state)).catch(error=>{status.error=error.message;});},60);
  }
  async function execute(command){
    if(completed.has(command.id)){await post(`/api/sessions/${session}/results`,completed.get(command.id));return;}
    executing=true;clearTimeout(reportTimer);let result;
    try{
      capture();
      if(Date.now()>command.expires_at)throw Object.assign(new Error('Command expired before execution.'),{code:'command_expired'});
      if(command.expected_revision!==revision)throw Object.assign(new Error('The page changed after the command was planned. Retry with its current state.'),{code:'state_conflict'});
      let last;
      for(const action of command.actions){last=await call(action.tool,action.arguments);if(!last?.ok)throw new Error(last?.error??'The page rejected this operation.');}
      result={id:command.id,ok:true,result:last,...capture()};
    }catch(error){result={id:command.id,ok:false,error:error.message,code:error.code??'page_error',...capture()};}
    finally{executing=false;}
    completed.set(command.id,result);if(completed.size>256)completed.delete(completed.keys().next().value);
    await posts.catch(()=>{});
    await post(`/api/sessions/${session}/results`,result);
  }
  async function connect(){
    if(stopped)return;
    status.state='connecting';stream?.close();
    try{
      const r=await fetch('/api/connect',{method:'POST',credentials:'same-origin',headers:{'Content-Type':'application/json'},body:JSON.stringify({session_id:storageGet()})});
      if(r.status===404||r.status===405){status.state='static';return;}
      if(!r.ok)throw new Error(`Bridge registration: HTTP ${r.status}`);
      const connected=await r.json();session=connected.session_id;storageSet(session);revision=connected.revision;signature='';
      status.session_id=session;status.error=null;
      await post(`/api/sessions/${session}/state`,capture());
      stream=new EventSource(`/api/sessions/${session}/events`);
      stream.onopen=()=>{status.state='connected';status.error=null;report();};
      stream.addEventListener('command',event=>{const command=JSON.parse(event.data);commands=commands.catch(()=>{}).then(()=>execute(command)).catch(error=>{status.error=error.message;});});
      stream.onerror=()=>{status.state='disconnected';stream.close();clearTimeout(retryTimer);retryTimer=setTimeout(connect,1000);};
    }catch(error){status.state='disconnected';status.error=error.message;retryTimer=setTimeout(connect,1500);}
  }
  const unsubscribe=subscribe(report);
  for(const event of ['scroll','change','click','keyup','place:report-state'])window.addEventListener(event,report,{passive:true});
  window.addEventListener('pagehide',()=>{stopped=true;stream?.close();clearTimeout(retryTimer);clearTimeout(reportTimer);unsubscribe();});
  window.addEventListener('pageshow',event=>{if(event.persisted){stopped=false;connect();}});
  connect();return status;
}
