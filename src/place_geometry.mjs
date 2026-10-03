import { Shape, Path, Vector2, ShapeUtils } from 'three';

// Local equirectangular projection. Scene distances are kilometres, not degrees.
const EARTH_METERS_PER_DEGREE = 111320;
export function projectPoint([longitude, latitude], [lon0, lat0]) {
  return [(longitude - lon0) * EARTH_METERS_PER_DEGREE * Math.cos(lat0 * Math.PI / 180) / 1000,
    -(latitude - lat0) * EARTH_METERS_PER_DEGREE / 1000];
}
export function unprojectPoint([x, z], [lon0, lat0]) {
  return [lon0 + x * 1000 / (EARTH_METERS_PER_DEGREE * Math.cos(lat0 * Math.PI / 180)),
    lat0 - z * 1000 / EARTH_METERS_PER_DEGREE];
}
export function polygonParts(geometry) {
  if (!geometry) return [];
  if (geometry.type === 'Polygon') return [geometry.coordinates];
  if (geometry.type === 'MultiPolygon') return geometry.coordinates;
  return [];
}
export function projectedRings(geometry, center) {
  return polygonParts(geometry).map(polygon => polygon.map(ring => {
    const points = ring.filter(c => Array.isArray(c) && Number.isFinite(c[0]) && Number.isFinite(c[1]))
      .map(c => { const [x, z] = projectPoint(c, center); return new Vector2(x, -z); });
    if (points.length > 1 && points[0].equals(points.at(-1))) points.pop();
    return points;
  })).filter(rings => rings[0]?.length >= 3);
}
export function geometryToShapes(geometry, center) {
  return projectedRings(geometry, center).map(rings => {
    const outer = rings[0].slice();
    if (!ShapeUtils.isClockWise(outer)) outer.reverse();
    const shape = new Shape(outer);
    for (const source of rings.slice(1)) {
      if (source.length < 3) continue;
      const hole = source.slice();
      if (ShapeUtils.isClockWise(hole)) hole.reverse();
      shape.holes.push(new Path(hole));
    }
    return shape;
  });
}
export function projectedBounds(city) {
  if (city.bounds?.length === 4 && city.bounds.every(Number.isFinite)) {
    const [west, south, east, north] = city.bounds;
    const [minX, maxZ] = projectPoint([west, south], city.center);
    const [maxX, minZ] = projectPoint([east, north], city.center);
    return {minX, maxX, minZ, maxZ};
  }
  const points = (city.features || []).flatMap(f => polygonParts(f.geometry).flat(2))
    .filter(c => Array.isArray(c) && Number.isFinite(c[0]) && Number.isFinite(c[1]))
    .map(c => projectPoint(c, city.center));
  if (!points.length) return {minX: -5, maxX: 5, minZ: -5, maxZ: 5};
  return {minX: Math.min(...points.map(p => p[0])), maxX: Math.max(...points.map(p => p[0])),
    minZ: Math.min(...points.map(p => p[1])), maxZ: Math.max(...points.map(p => p[1]))};
}
