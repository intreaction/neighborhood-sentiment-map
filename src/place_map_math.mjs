// Local geographic projection in kilometres, with north at the top of the map.
const KM_PER_DEGREE = 111.32;
export function projectPoint([longitude, latitude], [lon0, lat0]) {
  return [(longitude-lon0)*KM_PER_DEGREE*Math.cos(lat0*Math.PI/180), -(latitude-lat0)*KM_PER_DEGREE];
}
export function unprojectPoint([x,y], [lon0,lat0]) {
  return [lon0+x/(KM_PER_DEGREE*Math.cos(lat0*Math.PI/180)),lat0-y/KM_PER_DEGREE];
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
