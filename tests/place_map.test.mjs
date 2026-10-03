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
