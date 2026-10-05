// Spatial and page navigation for voice or keyboard agents. Pure functions; the
// browser side (place_navigator.js) applies the result with scrolling and focus.
export const SECTIONS=[
  {key:'map',label:'Map',left_right:'neighboring ZIP to the west or east'},
  {key:'zip_profile',label:'ZIP profile',left_right:'previous or next measure (the map switches to that measure)'},
  {key:'past_projects',label:'Past projects',left_right:'previous or next kind of project'},
  {key:'project_charts',label:'Project charts',left_right:'previous or next chart'},
  {key:'notes',label:'Notes and sources',left_right:'nothing to step through'}
];
export const CHART_TABS=[['engagement','Business engagement'],['sentiment','Sentiment'],['access','Negative access'],['realm','Negative public space'],['topics','Topics']];
export const COMPASS={north:[0,1],south:[0,-1],east:[1,0],west:[-1,0]};

// Wraps at the ends so "next" past the last item returns to the first.
export function stepIndex(length,index,delta){
  if(!length)return -1;
  if(index<0)index=delta>0?-1:length;  // nothing selected: count from just outside the ends
  return (((index+delta)%length)+length)%length;
}

// Nearest ZIP whose anchor lies within 60° of the compass direction from the current ZIP.
// Longitude is scaled by cos(latitude) so east-west and north-south distances compare.
export function neighborZip(anchors,zip,direction){
  const from=anchors[zip],dir=COMPASS[direction];
  if(!from||!dir)return null;
  const k=Math.cos(from[1]*Math.PI/180);
  let best=null,bestDistance=Infinity;
  for(const [other,to] of Object.entries(anchors)){
    if(other===zip)continue;
    const dx=(to[0]-from[0])*k,dy=to[1]-from[1],d=Math.hypot(dx,dy);
    if(!d)continue;
    const cos=(dx*dir[0]+dy*dir[1])/d;
    if(cos<Math.cos(Math.PI/3))continue;
    // Prefer ZIPs straight ahead: distance grows as the angle widens.
    const score=d/cos;
    if(score<bestDistance){bestDistance=score;best=other;}
  }
  return best;
}
