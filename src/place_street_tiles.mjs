import {projectPoint,unprojectPoint,screenPoint,worldPoint} from './place_map_math.mjs';

const WORLD_KM=40075.016686;
export function tileCoordinate([lon,lat],z) {
  const n=2**z, radians=Math.max(-85.05112878,Math.min(85.05112878,lat))*Math.PI/180;
  return [(lon+180)/360*n,(1-Math.asinh(Math.tan(radians))/Math.PI)/2*n];
}
export function tileCorner(x,y,z) {
  const n=2**z;
  return [x/n*360-180,Math.atan(Math.sinh(Math.PI*(1-2*y/n)))*180/Math.PI];
}
export function streetTiles(view,center,width,height) {
  const z=Math.max(0,Math.min(19,Math.round(Math.log2(view.scale*WORLD_KM*Math.cos(center[1]*Math.PI/180)/256))));
  const nw=tileCoordinate(unprojectPoint(worldPoint([0,0],view,width,height),center),z);
  const se=tileCoordinate(unprojectPoint(worldPoint([width,height],view,width,height),center),z);
  const tiles=[],n=2**z;
  for(let y=Math.max(0,Math.floor(nw[1]));y<=Math.min(n-1,Math.floor(se[1]));y++) {
    for(let x=Math.max(0,Math.floor(nw[0]));x<=Math.min(n-1,Math.floor(se[0]));x++) {
      const a=screenPoint(projectPoint(tileCorner(x,y,z),center),view,width,height);
      const b=screenPoint(projectPoint(tileCorner(x+1,y+1,z),center),view,width,height);
      tiles.push({key:`${z}/${x}/${y}`,x:a[0],y:a[1],width:b[0]-a[0],height:b[1]-a[1]});
    }
  }
  return tiles;
}

// Request only the settled viewport. Native image loading honors HTTP cache headers.
export function createStreetTiles({redraw,onStatus=()=>{},makeImage=()=>new Image()}) {
  const cache=new Map();
  let enabled=true,disposed=false,timer=null,wanted=[],signature='',lastStatus='';
  function status(message){if(message!==lastStatus){lastStatus=message;onStatus(message);}}
  function load() {
    timer=null;
    if(disposed||!enabled)return;
    for(const tile of wanted) {
      if(cache.has(tile.key))continue;
      const image=makeImage(),entry={image,ready:false,failed:false};
      cache.set(tile.key,entry);
      image.referrerPolicy='strict-origin-when-cross-origin';
      image.onload=()=>{entry.ready=true;if(!disposed)redraw();};
      image.onerror=()=>{entry.failed=true;if(!disposed)redraw();};
      image.src=`https://tile.openstreetmap.org/${tile.key}.png`;
    }
    const visible=new Set(wanted.map(t=>t.key));
    for(const key of cache.keys()) {
      if(cache.size<=128)break;
      if(!visible.has(key)){const entry=cache.get(key);entry.image.onload=entry.image.onerror=null;cache.delete(key);}
    }
  }
  return {
    draw(ctx,view,center,width,height) {
      if(!enabled){status('Offline boundaries · no street-map connection needed.');return;}
      wanted=streetTiles(view,center,width,height);
      const next=wanted.map(t=>t.key).join('|');
      if(next!==signature){signature=next;clearTimeout(timer);timer=setTimeout(load,180);}
      let loaded=0,failed=0;
      ctx.save();ctx.filter=globalThis.matchMedia?.('(prefers-color-scheme: dark)').matches?'invert(1) hue-rotate(180deg) saturate(0.35) brightness(0.82) contrast(0.92)':'saturate(0.45)';
      for(const tile of wanted) {
        const entry=cache.get(tile.key);
        if(entry?.ready){ctx.drawImage(entry.image,tile.x,tile.y,tile.width+.5,tile.height+.5);loaded++;}
        else if(entry?.failed)failed++;
      }
      ctx.restore();
      status(failed?'Some street detail is unavailable; offline boundaries fill the gaps. Switch Offline / Streets to retry.':loaded===wanted.length?'Street detail · OpenStreetMap · zoom in for streets and buildings.':'Loading street detail… Offline boundaries remain available.');
    },
    setEnabled(value){enabled=value;clearTimeout(timer);signature='';for(const [key,entry] of cache)if(entry.failed)cache.delete(key);redraw();},
    dispose(){disposed=true;clearTimeout(timer);for(const entry of cache.values())entry.image.onload=entry.image.onerror=null;cache.clear();}
  };
}
