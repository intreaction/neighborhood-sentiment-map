import test from 'node:test';
import assert from 'node:assert/strict';
import {stepIndex,neighborZip} from '../src/place_navigation.mjs';

test('stepIndex wraps and starts from the ends when nothing is selected',()=>{
  assert.equal(stepIndex(3,-1,1),0);assert.equal(stepIndex(3,-1,-1),2);assert.equal(stepIndex(10,-1,3),2);assert.equal(stepIndex(10,-1,-2),8);
  assert.equal(stepIndex(3,2,1),0);assert.equal(stepIndex(3,0,-1),2);assert.equal(stepIndex(0,0,1),-1);
});
test('neighborZip picks the closest ZIP in the compass direction',()=>{
  const anchors={a:[0,0],east:[1,0.1],far_east:[3,0],north:[0,1],diagonal:[1,1.2]};
  assert.equal(neighborZip(anchors,'a','east'),'east');
  assert.equal(neighborZip(anchors,'a','north'),'north');
  assert.equal(neighborZip(anchors,'a','west'),null);
  assert.equal(neighborZip(anchors,'missing','east'),null);
});
