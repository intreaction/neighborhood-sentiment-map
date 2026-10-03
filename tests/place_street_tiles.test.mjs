import test from 'node:test';
import assert from 'node:assert/strict';
import {tileCoordinate,tileCorner,streetTiles,createStreetTiles} from '../src/place_street_tiles.mjs';
import {projectPoint,screenPoint} from '../src/place_map_math.mjs';

test('street tile pixels align with geographic overlays across all five metros',()=>{
  for(const center of [[-75.16,39.95],[-82.46,27.95],[-86.78,36.16],[-90.07,29.95],[-110.97,32.22]]) {
    for(const scale of [10,150,1600]) {
      const view={x:0,y:0,scale},tiles=streetTiles(view,center,680,390);
      assert.ok(tiles.length>0&&tiles.length<40);
      const z=Number(tiles[0].key.split('/')[0]);
      const [tx,ty]=tileCoordinate(center,z),x=Math.floor(tx),y=Math.floor(ty);
      const tile=tiles.find(t=>t.key===`${z}/${x}/${y}`);
      const pixel=[tile.x+(tx-x)*tile.width,tile.y+(ty-y)*tile.height];
      assert.ok(Math.abs(pixel[0]-340)<1e-7);
      assert.ok(Math.abs(pixel[1]-195)<1e-7);
      const corner=tileCorner(x,y,z);
      assert.deepEqual(screenPoint(projectPoint(corner,center),view,680,390),[tile.x,tile.y]);
    }
  }
});

test('street tiles load only the settled viewport, reuse images, and stop in offline mode',async()=>{
  const images=[],statuses=[],drawn=[];
  const layer=createStreetTiles({redraw:()=>{},onStatus:s=>statuses.push(s),makeImage:()=>{const img={};images.push(img);return img;}});
  const ctx={save(){},restore(){},drawImage(...args){drawn.push(args);}};
  const center=[-75.16,39.95],view={x:0,y:0,scale:150};
  layer.draw(ctx,view,center,680,390);
  layer.draw(ctx,{...view,x:20},center,680,390);
  assert.equal(images.length,0);
  await new Promise(r=>setTimeout(r,200));
  const count=images.length;
  assert.equal(count,streetTiles({...view,x:20},center,680,390).length);
  for(const img of images){assert.match(img.src,/^https:\/\/tile.openstreetmap.org\//);assert.equal(img.referrerPolicy,'strict-origin-when-cross-origin');img.onload();}
  layer.draw(ctx,{...view,x:20},center,680,390);
  assert.equal(drawn.length,count);
  assert.match(statuses.at(-1),/^Street detail/);
  assert.equal(images.length,count);
  layer.setEnabled(false);
  layer.draw(ctx,view,center,680,390);
  await new Promise(r=>setTimeout(r,200));
  assert.equal(images.length,count);
  assert.match(statuses.at(-1),/^Offline boundaries/);
  layer.dispose();
});

test('failed street requests leave a fallback and can be retried explicitly',async()=>{
  const images=[],statuses=[];
  const layer=createStreetTiles({redraw:()=>{},onStatus:s=>statuses.push(s),makeImage:()=>{const img={};images.push(img);return img;}});
  const ctx={save(){},restore(){},drawImage(){}};
  const view={x:0,y:0,scale:150},center=[-75.16,39.95];
  layer.draw(ctx,view,center,680,390);
  await new Promise(r=>setTimeout(r,200));
  for(const img of images)img.onerror();
  layer.draw(ctx,view,center,680,390);
  assert.match(statuses.at(-1),/unavailable.*offline boundaries/);
  const count=images.length;
  layer.setEnabled(false);layer.setEnabled(true);
  layer.draw(ctx,view,center,680,390);
  await new Promise(r=>setTimeout(r,200));
  assert.equal(images.length,count*2);
  layer.dispose();
});
