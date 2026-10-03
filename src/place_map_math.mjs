// Web Mercator, scaled to local kilometres at the city center.
// Sharing the basemap projection keeps street tiles, business dots and clicks aligned.
const RADIUS_KM = 6378.137;
const rad = Math.PI / 180;
const mercatorY = latitude => Math.asinh(Math.tan(Math.max(-85.05112878,Math.min(85.05112878,latitude))*rad));
export function projectPoint([longitude, latitude], [lon0, lat0]) {
  const scale=RADIUS_KM*Math.cos(lat0*rad);
  return [(longitude-lon0)*rad*scale, -(mercatorY(latitude)-mercatorY(lat0))*scale];
}
export function unprojectPoint([x,y], [lon0,lat0]) {
  const scale=RADIUS_KM*Math.cos(lat0*rad);
  return [lon0+x/(rad*scale), Math.atan(Math.sinh(mercatorY(lat0)-y/scale))/rad];
}
export function polygonParts(geometry) {
  return geometry?.type==='Polygon' ? [geometry.coordinates] : geometry?.type==='MultiPolygon' ? geometry.coordinates : [];
}
export function fitView(bounds,center,width,height,padding=28) {
  const [left,bottom]=projectPoint(bounds.slice(0,2),center);
  const [right,top]=projectPoint(bounds.slice(2,4),center);
  return {x:(left+right)/2,y:(top+bottom)/2,scale:Math.min((width-padding*2)/(right-left),(height-padding*2)/(bottom-top))};
}
export function screenPoint([x,y],view,width,height) {
  return [(x-view.x)*view.scale+width/2,(y-view.y)*view.scale+height/2];
}
export function worldPoint([x,y],view,width,height) {
  return [(x-width/2)/view.scale+view.x,(y-height/2)/view.scale+view.y];
}

// Keep the viewport within the city overview plus a full city width on each side and half a city height above/below.
// At wide aspect ratios the overview necessarily includes extra surroundings.
export function constrainCityView(view,bounds,center,width,height,insetLeft=0){
  if(insetLeft>0){
    const visible=constrainCityView({...view,x:view.x+insetLeft/(2*view.scale)},bounds,center,Math.max(100,width-insetLeft),height);
    return {...visible,x:visible.x-insetLeft/(2*visible.scale)};
  }
  const overview=fitView(bounds,center,width,height);
  const maxScale=256*2**19/(40075.016686*Math.cos(center[1]*rad));
  const scale=Math.max(overview.scale,Math.min(maxScale,view.scale));
  const [left,bottom]=projectPoint(bounds.slice(0,2),center);
  const [right,top]=projectPoint(bounds.slice(2,4),center);
  const extentX=Math.max((right-left)/2,width/(2*overview.scale))+(right-left);
  const extentY=Math.max((bottom-top)/2,height/(2*overview.scale))+(bottom-top)*.5;
  const roomX=Math.max(0,extentX-width/(2*scale));
  const roomY=Math.max(0,extentY-height/(2*scale));
  return {x:Math.max(overview.x-roomX,Math.min(overview.x+roomX,view.x)),
    y:Math.max(overview.y-roomY,Math.min(overview.y+roomY,view.y)),scale};
}


export function fitUnobscuredView(bounds,center,width,height,insetLeft=0,padding=28){
  const view=fitView(bounds,center,Math.max(100,width-insetLeft),height,padding);
  return {...view,x:view.x-insetLeft/(2*view.scale)};
}
