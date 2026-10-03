import {FOCUSES,areaValue,areaColor,formatAreaValue,areaAt} from './place_area_math.mjs';
import {createStreetTiles} from './place_street_tiles.mjs';
import {projectPoint,unprojectPoint,polygonParts,fitView,fitUnobscuredView,constrainCityView,screenPoint,worldPoint} from './place_map_math.mjs';

/** Local 2D map: real ZIP boundaries, business observations and proposal catchment. */
export async function createPlaceMap({container,onPick=()=>{},onStatus=()=>{},onBasemapStatus=()=>{},getLeftInset=()=>0}={}) {
  if(!container)throw new Error('A map container is required.');
  const canvas=document.createElement('canvas');
  canvas.className='place-map-canvas';canvas.tabIndex=0;
  canvas.setAttribute('role','img');
  canvas.setAttribute('aria-label','2D city map. Drag to pan, scroll to zoom, click to select a ZIP. Use arrow keys to pan, plus and minus to zoom, or the coordinate form to select a location.');
  const ctx=canvas.getContext('2d');
  if(!ctx)throw new Error('2D graphics are unavailable.');
  container.append(canvas);
  const attribution=document.createElement('a');
  attribution.className='map-attribution';attribution.href='https://www.openstreetmap.org/copyright';
  attribution.target='_blank';attribution.rel='noopener';attribution.textContent='© OpenStreetMap contributors';
  container.append(attribution);
  const tooltip=document.createElement('div');tooltip.className='area-map-tooltip';tooltip.hidden=true;container.append(tooltip);
  const hatch=document.createElement('canvas');hatch.width=8;hatch.height=8;
  const hctx=hatch.getContext('2d');hctx.strokeStyle='#445a5866';hctx.lineWidth=1;hctx.beginPath();hctx.moveTo(0,8);hctx.lineTo(8,0);hctx.stroke();
  const missingPattern=ctx.createPattern(hatch,'repeat');
  let city,selection,view,width=1,height=1,leftInset=0,drag=null,disposed=false,frame=null;
  let showBusinesses=false,heatFocus='none',heatAreas=new Map(),selectedArea=null;
  const streetLayer=createStreetTiles({redraw:schedule,onStatus:onBasemapStatus});
  let polygons=[],businesses=[];
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
      ctx.strokeStyle=city.features[index].properties.zip===selectedArea?'#173c35':'#a7bba9';ctx.lineWidth=city.features[index].properties.zip===selectedArea?2.5:.7;ctx.stroke();
    });
    streetLayer.draw(ctx,view,city.center,width,height);
    if(heatFocus!=='none')polygons.forEach((parts,index)=>{
      const zip=city.features[index].properties.zip,value=areaValue(heatAreas.get(zip),heatFocus);
      ctx.beginPath();
      for(const rings of parts)for(const ring of rings){ring.forEach((point,i)=>{const [x,y]=screen(point);if(i)ctx.lineTo(x,y);else ctx.moveTo(x,y);});ctx.closePath();}
      ctx.save();ctx.globalAlpha=value===null?.25:.5;ctx.fillStyle=areaColor(value,heatFocus);ctx.fill('evenodd');ctx.restore();
      if(value===null&&missingPattern){ctx.fillStyle=missingPattern;ctx.fill('evenodd');}
      ctx.strokeStyle=zip===selectedArea?'#173c35':'#6d625075';ctx.lineWidth=zip===selectedArea?2.5:.8;ctx.stroke();
    });
    ctx.fillStyle='#245647b3';ctx.beginPath();
    for(const point of showBusinesses?businesses:[]) {
      const [x,y]=screen(point);if(x<0||x>width||y<0||y>height)continue;
      ctx.moveTo(x+1.7,y);ctx.arc(x,y,1.7,0,Math.PI*2);
    }
    ctx.fill();
    // Scale bar and north indicator stay readable at every zoom level.
    const target=85/view.scale,power=10**Math.floor(Math.log10(target));
    const km=[1,2,5,10].map(n=>n*power).find(n=>n>=target)||power*10;
    const pixels=km*view.scale;
    ctx.fillStyle='#fffdf6e8';ctx.fillRect(12,height-36,pixels+20,27);
    ctx.strokeStyle='#386451';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(22,height-17);ctx.lineTo(22+pixels,height-17);ctx.stroke();
    ctx.fillStyle='#204a3b';ctx.font='10px system-ui';ctx.fillText(km>=1?`${km} km`:`${Math.round(km*1000)} m`,22,height-23);
    ctx.font='bold 12px system-ui';ctx.fillText('N ↑',width-39,25);
  }
  function schedule(){if(city&&view)view=constrainCityView(view,city.bounds,city.center,width,height,leftInset);if(!disposed&&frame===null)frame=requestAnimationFrame(draw);}
  function reset(){if(!city)return;view=fitUnobscuredView(city.bounds,city.center,width,height,leftInset);schedule();}
  function resize(){
    width=Math.max(100,container.clientWidth);height=Math.max(100,container.clientHeight);
    leftInset=Math.min(Math.max(0,getLeftInset()),Math.max(0,width-200));
    const ratio=Math.min(window.devicePixelRatio||1,2);canvas.width=Math.round(width*ratio);canvas.height=Math.round(height*ratio);ctx.setTransform(ratio,0,0,ratio,0,0);
    if(!view)reset();else schedule();
  }
  const observer=new ResizeObserver(resize);observer.observe(container);resize();
  function eventPoint(event){const r=canvas.getBoundingClientRect();return [event.clientX-r.left,event.clientY-r.top];}
  function zoom(factor,at=[(width+leftInset)/2,height/2]) {
    if(!view||!city)return;
    const before=worldPoint(at,view,width,height),base=fitUnobscuredView(city.bounds,city.center,width,height,leftInset).scale;
    view.scale=Math.max(base,Math.min(256*2**19/(40075.016686*Math.cos(city.center[1]*Math.PI/180)),view.scale*factor));
    const after=worldPoint(at,view,width,height);view.x+=before[0]-after[0];view.y+=before[1]-after[1];schedule();
  }
  function down(e){if(e.button!==0||!view)return;drag={start:eventPoint(e),view:{...view},moved:false,id:e.pointerId};canvas.setPointerCapture(e.pointerId);}
  function move(e){
    if(!drag&&city&&view){
      if(heatFocus==='none'){tooltip.hidden=true;return;}
      const p=eventPoint(e),geo=unprojectPoint(worldPoint(p,view,width,height),city.center),zip=areaAt(geo,city.features||[]);
      tooltip.hidden=!zip;
      if(zip){tooltip.textContent=`ZIP ${zip} · ${FOCUSES[heatFocus].title}: ${formatAreaValue(areaValue(heatAreas.get(zip),heatFocus),heatFocus)}`;tooltip.style.left=Math.max(8,Math.min(p[0]+12,width-240))+'px';tooltip.style.top=Math.max(8,Math.min(p[1]+12,height-65))+'px';}
      return;
    }
    tooltip.hidden=true;
    if(!drag||e.pointerId!==drag.id)return;const p=eventPoint(e),dx=p[0]-drag.start[0],dy=p[1]-drag.start[1];if(Math.hypot(dx,dy)>5)drag.moved=true;if(drag.moved){view.x=drag.view.x-dx/view.scale;view.y=drag.view.y-dy/view.scale;schedule();drag.start=p;drag.view={...view};}}
  function up(e){
    if(!drag||e.pointerId!==drag.id)return;const clicked=!drag.moved;drag=null;
    if(canvas.hasPointerCapture(e.pointerId))canvas.releasePointerCapture(e.pointerId);
    if(!clicked||!city)return;
    const point=eventPoint(e);
    const [longitude,latitude]=unprojectPoint(worldPoint(point,view,width,height),city.center);
    onPick({longitude,latitude,radiusMeters:500,cityId:city.id});
  }
  function cancel(){drag=null;}
  function leave(){tooltip.hidden=true;}
  function wheel(e){e.preventDefault();zoom(Math.exp(-Math.max(-100,Math.min(100,e.deltaY))*.008),eventPoint(e));}
  function key(e){
    if(!view)return;
    if(['+','=','-','ArrowLeft','ArrowRight','ArrowUp','ArrowDown','Home'].includes(e.key))e.preventDefault();
    if(e.key==='+'||e.key==='=')zoom(1.5);else if(e.key==='-')zoom(1/1.5);else if(e.key==='Home')reset();
    else {const offsets={ArrowLeft:[-60,0],ArrowRight:[60,0],ArrowUp:[0,-60],ArrowDown:[0,60]};const d=offsets[e.key];if(d){view.x+=d[0]/view.scale;view.y+=d[1]/view.scale;schedule();}}
  }
  canvas.addEventListener('pointerleave',leave);canvas.addEventListener('pointerdown',down);canvas.addEventListener('pointermove',move);canvas.addEventListener('pointerup',up);canvas.addEventListener('pointercancel',cancel);canvas.addEventListener('wheel',wheel,{passive:false});canvas.addEventListener('keydown',key);
  return {
    setCity(value){
      city=value;selection=null;selectedArea=null;tooltip.hidden=true;
      polygons=(city.features||[]).map(f=>polygonParts(f.geometry).map(p=>p.map(r=>r.map(point=>projectPoint(point,city.center)))));
      businesses=(city.businesses||[]).filter(b=>b[2]>0&&b[0]>=city.bounds[0]&&b[0]<=city.bounds[2]&&b[1]>=city.bounds[1]&&b[1]<=city.bounds[3]).map(b=>projectPoint(b,city.center));
      reset();report('Drag to pan · Scroll or use + / − to zoom · Click a ZIP to select its boundary · Panning stays near this city.');
    },
    setHeatmap(focus,areas,zip){heatFocus=focus;heatAreas=new Map(areas.map(a=>[a.zip,a]));selectedArea=zip;tooltip.hidden=true;schedule();},
    focusArea(zip){
      const f=(city?.features||[]).find(f=>f.properties.zip===zip);if(!f)return;
      const points=polygonParts(f.geometry).flat(2),xs=points.map(p=>p[0]),ys=points.map(p=>p[1]);
      view=fitUnobscuredView([Math.min(...xs),Math.min(...ys),Math.max(...xs),Math.max(...ys)],city.center,width,height,leftInset,50);selectedArea=zip;schedule();
    },
    setSelection(value){selection=value;schedule();},
    focusSelection(){if(!selection||!city)return;if(selection.zip){this.focusArea(selection.zip);return;}const [x,y]=projectPoint([selection.longitude,selection.latitude],city.center);const scale=Math.min(width-leftInset,height)/2.6;view={x:x-leftInset/(2*scale),y,scale};schedule();},
    setBasemap(value){streetLayer.setEnabled(value==='streets');attribution.hidden=value!=='streets';},
    setBusinesses(value){showBusinesses=value;schedule();},
    reset,zoomIn(){zoom(1.5);},zoomOut(){zoom(1/1.5);},
    dispose(){disposed=true;streetLayer.dispose();attribution.remove();tooltip.remove();canvas.removeEventListener('pointerleave',leave);observer.disconnect();if(frame!==null)cancelAnimationFrame(frame);canvas.removeEventListener('pointerdown',down);canvas.removeEventListener('pointermove',move);canvas.removeEventListener('pointerup',up);canvas.removeEventListener('pointercancel',cancel);canvas.removeEventListener('wheel',wheel);canvas.removeEventListener('keydown',key);canvas.remove();}
  };
}
