import {projectPoint,unprojectPoint,polygonParts,fitView,screenPoint,worldPoint} from './place_map_math.mjs';

/** Local 2D map: real ZIP boundaries, business observations and proposal catchment. */
export async function createPlaceMap({container,onPick=()=>{},onStatus=()=>{}}={}) {
  if(!container)throw new Error('A map container is required.');
  const canvas=document.createElement('canvas');
  canvas.className='place-map-canvas';canvas.tabIndex=0;
  canvas.setAttribute('role','img');
  canvas.setAttribute('aria-label','2D city map. Drag to pan, scroll to zoom, click to place a proposal. Use arrow keys to pan, plus and minus to zoom, or the coordinate form to select a location.');
  const ctx=canvas.getContext('2d');
  if(!ctx)throw new Error('2D graphics are unavailable.');
  container.append(canvas);
  let city,selection,view,width=1,height=1,drag=null,disposed=false,frame=null;
  let polygons=[],businesses=[],projects=[],landmarkHits=[];
  const report=message=>onStatus({message});
  const screen=point=>screenPoint(point,view,width,height);
  function draw() {
    frame=null;if(disposed||!city||!view)return;
    ctx.clearRect(0,0,width,height);ctx.fillStyle='#e8eee9';ctx.fillRect(0,0,width,height);
    const colors=['#d7e4d6','#cddfcf','#e0e9da','#d3e1ce'];
    polygons.forEach((parts,index)=>{
      ctx.beginPath();
      for(const rings of parts)for(const ring of rings) {
        ring.forEach((point,i)=>{const [x,y]=screen(point);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});ctx.closePath();
      }
      ctx.fillStyle=colors[index%colors.length];ctx.fill('evenodd');
      ctx.strokeStyle='#a7bba9';ctx.lineWidth=.7;ctx.stroke();
    });
    ctx.fillStyle='#386451';ctx.beginPath();
    for(const point of businesses) {
      const [x,y]=screen(point);if(x<0||x>width||y<0||y>height)continue;
      ctx.moveTo(x+1.7,y);ctx.arc(x,y,1.7,0,Math.PI*2);
    }
    ctx.fill();
    if(selection) {
      const [x,y]=screen(projectPoint([selection.longitude,selection.latitude],city.center));
      const r=(selection.radiusMeters||500)/1000*view.scale;
      ctx.beginPath();ctx.arc(x,y,r,0,Math.PI*2);ctx.fillStyle='#edb27745';ctx.fill();
      ctx.strokeStyle='#b76a32';ctx.lineWidth=2;ctx.stroke();
      ctx.beginPath();ctx.arc(x,y,5,0,Math.PI*2);ctx.fillStyle='#b76a32';ctx.fill();ctx.strokeStyle='#fffdf6';ctx.stroke();
    }
    landmarkHits=[];ctx.font='11px system-ui';
    for(const project of projects) {
      const [x,y]=screen(project.point);if(x<10||x>width-10||y<30||y>height-35)continue;
      const label=project.name,w=ctx.measureText(label).width+14;
      const rect={x:x-w/2,y:y-25,w,h:20,project};
      if(landmarkHits.some(a=>rect.x<a.x+a.w&&rect.x+w>a.x&&rect.y<a.y+a.h&&rect.y+20>a.y))continue;
      ctx.fillStyle='#fffdf6';ctx.fillRect(rect.x,rect.y,w,20);ctx.strokeStyle='#a7bba9';ctx.lineWidth=1;ctx.strokeRect(rect.x,rect.y,w,20);
      ctx.fillStyle='#204a3b';ctx.fillText(label,rect.x+7,rect.y+14);
      ctx.beginPath();ctx.arc(x,y,3,0,Math.PI*2);ctx.fill();landmarkHits.push(rect);
    }
    // Scale bar and north indicator stay readable at every zoom level.
    const target=85/view.scale,power=10**Math.floor(Math.log10(target));
    const km=[1,2,5,10].map(n=>n*power).find(n=>n>=target)||power*10;
    const pixels=km*view.scale;
    ctx.fillStyle='#fffdf6e8';ctx.fillRect(12,height-36,pixels+20,27);
    ctx.strokeStyle='#386451';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(22,height-17);ctx.lineTo(22+pixels,height-17);ctx.stroke();
    ctx.fillStyle='#204a3b';ctx.font='10px system-ui';ctx.fillText(km>=1?`${km} km`:`${Math.round(km*1000)} m`,22,height-23);
    ctx.font='bold 12px system-ui';ctx.fillText('N ↑',width-39,25);
  }
  function schedule(){if(!disposed&&frame===null)frame=requestAnimationFrame(draw);}
  function reset(){if(!city)return;view=fitView(city.bounds,city.center,width,height);schedule();}
  function resize(){
    width=Math.max(100,container.clientWidth);height=Math.max(100,container.clientHeight);
    const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);
    if(!view)reset();else schedule();
  }
  const observer=new ResizeObserver(resize);observer.observe(container);resize();
  function eventPoint(event){const r=canvas.getBoundingClientRect();return [event.clientX-r.left,event.clientY-r.top];}
  function zoom(factor,at=[width/2,height/2]) {
    if(!view||!city)return;
    const before=worldPoint(at,view,width,height),base=fitView(city.bounds,city.center,width,height).scale;
    view.scale=Math.max(base*.6,Math.min(base*100,view.scale*factor));
    const after=worldPoint(at,view,width,height);view.x+=before[0]-after[0];view.y+=before[1]-after[1];schedule();
  }
  function down(e){if(e.button!==0||!view)return;drag={start:eventPoint(e),view:{...view},moved:false,id:e.pointerId};canvas.setPointerCapture(e.pointerId);}
  function move(e){if(!drag||e.pointerId!==drag.id)return;const p=eventPoint(e),dx=p[0]-drag.start[0],dy=p[1]-drag.start[1];if(Math.hypot(dx,dy)>5)drag.moved=true;if(drag.moved){view.x=drag.view.x-dx/view.scale;view.y=drag.view.y-dy/view.scale;schedule();}}
  function up(e){
    if(!drag||e.pointerId!==drag.id)return;const clicked=!drag.moved;drag=null;
    if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
    if(!clicked||!city)return;
    const point=eventPoint(e),hit=landmarkHits.find(r=>point[0]>=r.x&&point[0]<=r.x+r.w&&point[1]>=r.y&&point[1]<=r.y+r.h);
    const [longitude,latitude]=hit?hit.project.center:unprojectPoint(worldPoint(point,view,width,height),city.center);
    onPick({longitude,latitude,radiusMeters:500,cityId:city.id});
  }
  function cancel(){drag=null;}
  function wheel(e){e.preventDefault();zoom(Math.exp(-Math.max(-100,Math.min(100,e.deltaY))*.008),eventPoint(e));}
  function key(e){
    if(!view)return;
    if(['+','=','-','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))e.preventDefault();
    if(e.key==='+'||e.key==='=')zoom(1.5);else if(e.key==='-')zoom(1/1.5);else if(e.key==='Home')reset();
    else {const offsets={ArrowLeft:[-60,0],ArrowRight:[60,0],ArrowUp:[0,-60],ArrowDown:[0,60]};const d=offsets[e.key];if(d){view.x+=d[0]/view.scale;view.y+=d[1]/view.scale;schedule();}}
  }
  canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('keydown',key);
  return {
    setCity(value){
      city=value;selection=null;
      polygons=(city.features||[]).map(f=>polygonParts(f.geometry).map(p=>p.map(r=>r.map(point=>projectPoint(point,city.center)))));
      businesses=(city.businesses||[]).filter(b=>b[2]>0&&b[0]>=city.bounds[0]&&b[0]<=city.bounds[2]&&b[1]>=city.bounds[1]&&b[1]<=city.bounds[3]).map(b=>projectPoint(b,city.center));
      projects=(city.projects||[]).map(p=>({...p,point:projectPoint(p.center,city.center)}));
      reset();report('Drag to pan · Scroll or use + / − to zoom · Place near reviewed businesses.');
    },
    setSelection(value){selection=value;schedule();},
    focusSelection(){if(!selection||!city)return;const [x,y]=projectPoint([selection.longitude,selection.latitude],city.center);view={x,y,scale:Math.min(width,height)/2.6};schedule();},
    reset,zoomIn(){zoom(1.5);},zoomOut(){zoom(1/1.5);},
    dispose(){disposed=true;observer.disconnect();if(frame!==null)cancelAnimationFrame(frame);canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',up);canvas.removeEventListener('pointercancel',cancel);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('keydown',key);canvas.remove();}
  };
}
