import test from 'node:test';
import assert from 'node:assert/strict';
import { ShapeGeometry, Vector3 } from 'three';
import { projectPoint, unprojectPoint, geometryToShapes, projectedBounds } from '../src/place_geometry.mjs';

function triangleArea(geometry) {
  const position = geometry.getAttribute('position'), index = geometry.index;
  let area = 0;
  for (let i = 0; i < index.count; i += 3) {
    const a = new Vector3().fromBufferAttribute(position, index.getX(i));
    const b = new Vector3().fromBufferAttribute(position, index.getX(i + 1));
    const c = new Vector3().fromBufferAttribute(position, index.getX(i + 2));
    area += b.sub(a).cross(c.sub(a)).length() / 2;
  }
  return area;
}
const center = [-75, 40];
const corner = (x, z) => unprojectPoint([x, z], center);
const square = (x0, z0, x1, z1) => [corner(x0,z0),corner(x1,z0),corner(x1,z1),corner(x0,z1),corner(x0,z0)];

test('local kilometre projection roundtrips a geographic selection', () => {
  const point = [-75.16362, 39.9527];
  const actual = unprojectPoint(projectPoint(point, center), center);
  assert.ok(Math.abs(point[0] - actual[0]) < 1e-10);
  assert.ok(Math.abs(point[1] - actual[1]) < 1e-10);
  assert.ok(projectPoint([-75, 40.001], center)[1] < 0, 'North is negative scene Z');
});

test('GeoJSON polygon holes stay unfilled under either winding', () => {
  for (const reverse of [false,true]) {
    const outer=square(0,0,4,4), hole=square(1,1,3,3);
    const shapes=geometryToShapes({type:'Polygon',coordinates:reverse?[outer.reverse(),hole.reverse()]:[outer,hole]}, center);
    assert.equal(shapes.length,1);
    assert.equal(shapes[0].holes.length,1);
    const mesh=new ShapeGeometry(shapes);
    assert.ok(Math.abs(triangleArea(mesh)-12)<1e-7, '16 km² outer minus 4 km² hole');
    mesh.dispose();
  }
});

test('GeoJSON multipart islands remain separate shapes with correct area', () => {
  const shapes=geometryToShapes({type:'MultiPolygon',coordinates:[[square(0,0,1,1)],[square(2,2,4,4)]]}, center);
  assert.equal(shapes.length,2);
  const mesh=new ShapeGeometry(shapes);
  assert.ok(Math.abs(triangleArea(mesh)-5)<1e-7);
  mesh.dispose();
});

test('map extents use real coordinates when bounds are not supplied', () => {
  const bounds=projectedBounds({center,features:[{geometry:{type:'Polygon',coordinates:[square(-2,-3,4,5)]}}]});
  assert.ok(Math.abs(bounds.minX+2)<1e-7);
  assert.ok(Math.abs(bounds.maxZ-5)<1e-7);
});

test('all real city features triangulate, including holes and multipart geometry', async () => {
  const fs=await import('node:fs/promises');
  const data=JSON.parse(await fs.readFile(new URL('../web/place-map.json',import.meta.url),'utf8'));
  let count=0;
  for (const city of data.cities) {
    for (const feature of city.features) {
      const shapes=geometryToShapes(feature.geometry,city.center);
      assert.ok(shapes.length, `${city.id} ${feature.properties.zip}`);
      const geometry=new ShapeGeometry(shapes);
      assert.ok(triangleArea(geometry)>0);
      assert.ok([...geometry.attributes.position.array].every(Number.isFinite));
      geometry.dispose(); count++;
    }
  }
  assert.equal(count,196);
});
