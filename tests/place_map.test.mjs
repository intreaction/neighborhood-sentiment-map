import test from 'node:test';
import assert from 'node:assert/strict';
import {projectPoint,unprojectPoint,fitView,screenPoint,worldPoint,polygonParts} from '../src/place_map_math.mjs';

test('2D click coordinates roundtrip geography after panning and zooming',()=>{
  const center=[-75.16,39.95],point=[-75.155,39.957];
  const view={x:.4,y:-.2,scale:170};
  const screen=screenPoint(projectPoint(point,center),view,640,390);
  const result=unprojectPoint(worldPoint(screen,view,640,390),center);
  for(let i=0;i<2;i++)assert.ok(Math.abs(result[i]-point[i])<1e-10);
});
test('city view fits all bounds and keeps north above south',()=>{
  const bounds=[-75.3,39.8,-75,40.1],center=[-75.15,39.95];
  const view=fitView(bounds,center,600,350);
  const southwest=screenPoint(projectPoint(bounds.slice(0,2),center),view,600,350);
  const northeast=screenPoint(projectPoint(bounds.slice(2,4),center),view,600,350);
  for(const p of [southwest,northeast])assert.ok(p[0]>=27.9&&p[0]<=572.1&&p[1]>=27.9&&p[1]<=322.1);
  assert.ok(northeast[1]<southwest[1]);
});
test('2D boundaries preserve polygon holes and multipart islands',()=>{
  const outer=[[0,0],[2,0],[2,2],[0,0]],hole=[[.5,.5],[1,.5],[.5,1],[.5,.5]];
  assert.deepEqual(polygonParts({type:'Polygon',coordinates:[outer,hole]}),[[outer,hole]]);
  assert.equal(polygonParts({type:'MultiPolygon',coordinates:[[outer,hole],[outer]]}).length,2);
});

test('city constraints bound pan and zoom across metros and viewport sizes',async()=>{
  const {constrainCityView}=await import('../src/place_map_math.mjs');
  const {readFileSync}=await import('node:fs');
  const map=JSON.parse(readFileSync(new URL('../web/place-map.json',import.meta.url)));
  for(const city of map.cities)for(const [w,h] of [[1100,800],[1800,700]]){
    const home=fitView(city.bounds,city.center,w,h);
    assert.deepEqual(constrainCityView(home,city.bounds,city.center,w,h),home);
    const low=constrainCityView({...home,scale:home.scale/100},city.bounds,city.center,w,h);
    assert.equal(low.scale,home.scale);
    for(const sign of [-1,1]){
      const edge=constrainCityView({x:sign*1e8,y:sign*1e8,scale:home.scale*4},city.bounds,city.center,w,h);
      assert.ok(Math.abs(edge.x-home.x)<2*w/home.scale);
      assert.ok(Math.abs(edge.y-home.y)<h/home.scale);
      assert.deepEqual(constrainCityView(edge,city.bounds,city.center,w,h),edge);
      const inward={...edge,x:edge.x-sign*.01,y:edge.y-sign*.01};
      assert.deepEqual(constrainCityView(inward,city.bounds,city.center,w,h),inward);
    }
  }
});


test('overview permits a full city width horizontally and half a city height vertically',async()=>{
  const {constrainCityView,projectPoint}=await import('../src/place_map_math.mjs');
  const bounds=[-75.3,39.8,-74.9,40.1],center=[-75.1,39.95],w=1100,h=800;
  const home=fitView(bounds,center,w,h);
  const [left,bottom]=projectPoint(bounds.slice(0,2),center);
  const [right,top]=projectPoint(bounds.slice(2,4),center);
  const edge=constrainCityView({...home,x:1e8,y:1e8},bounds,center,w,h);
  assert.ok(Math.abs(edge.x-home.x-(right-left))<1e-9);
  assert.ok(Math.abs(edge.y-home.y-(bottom-top)*.5)<1e-9);
});

test('city and ZIP fits center inside the map space beside the panel',async()=>{
  const {fitUnobscuredView,constrainCityView}=await import('../src/place_map_math.mjs');
  const bounds=[-75.3,39.8,-74.9,40.1],center=[-75.1,39.95],w=1100,h=800,inset=408;
  const view=fitUnobscuredView(bounds,center,w,h,inset);
  const geographicCenter=fitView(bounds,center,w,h);
  const screen=screenPoint([geographicCenter.x,geographicCenter.y],view,w,h);
  assert.ok(Math.abs(screen[0]-(w+inset)/2)<1e-9);
  assert.ok(Math.abs(screen[1]-h/2)<1e-9);
  const constrained=constrainCityView(view,bounds,center,w,h,inset);
  assert.ok(Math.abs(constrained.x-view.x)<1e-9);
  assert.equal(constrained.scale,view.scale);
});
