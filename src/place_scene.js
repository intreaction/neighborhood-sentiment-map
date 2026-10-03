import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { geometryToShapes, projectPoint, unprojectPoint, projectedBounds } from './place_geometry.mjs';

/** Desktop map scene. Coordinates are geographic; local scene units are km. */
export async function createPlaceScene({container, onPick = () => {}, onStatus = () => {}} = {}) {
  if (!container) throw new Error('A scene container is required.');
  let disposed = false, city = null, extent = null, selection = null;
  let pointerStart = null;
  let boardSpan = 10, boardMid = new THREE.Vector3(), metrics = {};
  const capabilities = {webgl: false};
  const report = (type, message, extra = {}) => onStatus({mode: 'desktop', type, message, capabilities: {...capabilities}, ...extra});
  let renderer;
  try {
    renderer = new THREE.WebGLRenderer({antialias: true, alpha: true, powerPreference: 'high-performance'});
  } catch (error) {
    report('unsupported', '3D graphics are unavailable in this browser. Use the coordinate inputs and historical examples to continue.');
    return {setCity(value) { city = value; }, setSelection() {}, setMetrics() {}, focusSelection() {}, reset() {},
      getCapabilities: () => ({...capabilities}),
      dispose() { disposed = true; }};
  }
  capabilities.webgl = true;
  renderer.setPixelRatio(Math.min(globalThis.devicePixelRatio || 1, 2));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.0;
  renderer.domElement.style.cssText = 'display:block;width:100%;height:100%;touch-action:none;outline-offset:-4px';
  renderer.domElement.tabIndex = 0;
  renderer.domElement.setAttribute('role', 'img');
  renderer.domElement.setAttribute('aria-label', 'Three-dimensional ZIP boundary map. Drag to orbit; scroll to zoom; click to select a location. Use coordinate inputs for keyboard selection.');
  container.appendChild(renderer.domElement);
  const scene = new THREE.Scene();
  scene.background = new THREE.Color('#e8eee9');
  const camera = new THREE.PerspectiveCamera(43, 1, 0.005, 1000);
  const controls = new OrbitControls(camera, renderer.domElement);
  const coarsePointer = globalThis.matchMedia?.('(pointer: coarse)').matches || false;
  renderer.domElement.style.touchAction = coarsePointer ? 'pan-y' : 'none';
  controls.enableRotate = !coarsePointer; controls.enablePan = !coarsePointer;
  controls.enableDamping = true; controls.dampingFactor = 0.1;
  controls.screenSpacePanning = false; controls.maxPolarAngle = Math.PI * 0.46;
  controls.minPolarAngle = 0.12; controls.minDistance = 0.3; controls.maxDistance = 100;
  controls.listenToKeyEvents(renderer.domElement);
  scene.add(new THREE.HemisphereLight(0xffffff, 0x7d9487, 1.5));
  const sun = new THREE.DirectionalLight(0xfff3d7, 1.9); sun.position.set(-8, 16, 8); scene.add(sun);
  const anchor = new THREE.Group(); anchor.name = 'city-map-root'; scene.add(anchor);
  const map = new THREE.Group(); map.name = 'shared-city-map'; anchor.add(map);
  const geography = new THREE.Group(), marker = new THREE.Group(), labelGroup = new THREE.Group(), landmarks = new THREE.Group();
  let businessCloud = null; const landmarkLabels = [];
  geography.name = 'geographic-boundaries'; marker.name = 'selected-catchment'; labelGroup.name = 'analysis-label';
  landmarks.name = "documented-landmarks"; map.add(geography, marker, labelGroup, landmarks);
  const raycaster = new THREE.Raycaster(), pointer = new THREE.Vector2();
  let pickPlane = null, plateHeight = 0.05;

  function release(group) {
    const geometries = new Set(), materials = new Set(), textures = new Set();
    group.traverse(object => {
      if (object.geometry) geometries.add(object.geometry);
      for (const material of (Array.isArray(object.material) ? object.material : [object.material])) {
        if (material) { materials.add(material); if (material.map) textures.add(material.map); }
      }
    });
    geometries.forEach(g => g.dispose()); textures.forEach(t => t.dispose()); materials.forEach(m => m.dispose()); group.clear();
  }
  function resetCamera() {
    if (!extent) return;
    controls.target.copy(boardMid);
    camera.position.set(boardMid.x + boardSpan * 0.18, boardSpan * 0.88, boardMid.z + boardSpan * 0.94);
    camera.near = Math.max(0.001, boardSpan / 10000); camera.far = Math.max(100, boardSpan * 15); camera.updateProjectionMatrix();
    controls.minDistance = Math.max(0.12, boardSpan * 0.018); controls.maxDistance = boardSpan * 3;
    controls.update(); controls.saveState();
  }
  function resize() {
    if (disposed) return;
    const width = Math.max(1, container.clientWidth), height = Math.max(1, container.clientHeight || 500);
    renderer.setSize(width, height, false); camera.aspect = width / height; camera.updateProjectionMatrix();
  }
  const observer = new ResizeObserver(resize); observer.observe(container); resize();

  function updateLabel() {
    release(labelGroup); if (!city || !extent) return;
    const canvas = document.createElement('canvas'); canvas.width = 1024; canvas.height = 208;
    const ctx = canvas.getContext('2d');
    ctx.fillStyle = '#193e38'; ctx.fillRect(0, 0, 1024, 208);
    ctx.fillStyle = '#c4d9c8'; ctx.font = '24px sans-serif'; ctx.fillText('PUBLIC INVESTMENT MAP  /  ' + String(city.label || city.id).toUpperCase(), 30, 40);
    ctx.fillStyle = '#ffffff'; ctx.font = 'bold 38px sans-serif';
    const title = String(metrics.title || (selection ? 'Selected 500 m catchment' : 'Select a place to explore')).slice(0, 48);
    ctx.fillText(title, 30, 94);
    ctx.fillStyle = '#c4d9c8'; ctx.font = '25px sans-serif';
    const pieces = [];
    if (Number.isFinite(metrics.costMillions)) pieces.push('$' + metrics.costMillions.toLocaleString() + 'M proposal');
    if (Number.isFinite(metrics.businesses)) pieces.push(metrics.businesses.toLocaleString() + ' reviewed businesses');
    if (Number.isFinite(metrics.ce)) pieces.push((metrics.ce > 0 ? '+' : '') + metrics.ce.toFixed(1) + ' reviews / $1M');
    ctx.fillText(pieces.length ? pieces.join('  ·  ').slice(0, 85) : 'ZIP geometry · schematic extrusion · not building heights', 30, 143);
    ctx.font = '19px sans-serif'; ctx.fillStyle = '#a4bfad'; ctx.fillText(String(metrics.subtitle || 'Historical Yelp evidence · exploratory estimate, not financial ROI').slice(0, 98), 30, 182);
    const texture = new THREE.CanvasTexture(canvas); texture.colorSpace = THREE.SRGBColorSpace;
    const width = boardSpan * 0.72, height = width * canvas.height / canvas.width;
    const plane = new THREE.Mesh(new THREE.PlaneGeometry(width, height), new THREE.MeshStandardMaterial({map: texture, roughness: 1, metalness: 0}));
    plane.rotation.x = -Math.PI / 2; plane.position.set(boardMid.x, 0.012, extent.maxZ + boardSpan * 0.11); labelGroup.add(plane);
  }
  function setCity(value) {
    if (disposed || !value || !Array.isArray(value.center) || !value.center.every(Number.isFinite)) return false;
    city = value; selection = null; metrics = {}; release(geography); release(marker); release(landmarks); landmarkLabels.length = 0; businessCloud = null;
    extent = projectedBounds(city);
    const width = Math.max(1, extent.maxX - extent.minX), depth = Math.max(1, extent.maxZ - extent.minZ);
    boardSpan = Math.max(width, depth); boardMid.set((extent.minX + extent.maxX) / 2, 0, (extent.minZ + extent.maxZ) / 2);
    plateHeight = Math.max(0.018, boardSpan * 0.003);
    const base = new THREE.Mesh(new THREE.BoxGeometry(width + boardSpan * 0.08, plateHeight * 0.65, depth + boardSpan * 0.28),
      new THREE.MeshStandardMaterial({color: 0xd7e4df, roughness: 0.95}));
    base.position.set(boardMid.x, -plateHeight * 0.45, boardMid.z + boardSpan * 0.075); geography.add(base);
    const colors = [0x75a893, 0x88b59d, 0x9fbfab, 0x649b83, 0xacc9b3];
    let regionCount = 0;
    for (const [index, feature] of (city.features || []).entries()) {
      const shapes = geometryToShapes(feature.geometry, city.center); if (!shapes.length) continue;
      const geometry = new THREE.ExtrudeGeometry(shapes, {depth: plateHeight, bevelEnabled: false, curveSegments: 1, steps: 1});
      geometry.rotateX(-Math.PI / 2);
      const material = new THREE.MeshStandardMaterial({color: colors[index % colors.length], roughness: 0.9, metalness: 0.02});
      const mesh = new THREE.Mesh(geometry, material); mesh.name = 'ZIP ' + (feature.properties?.zip || index); geography.add(mesh);
      const edge = new THREE.LineSegments(new THREE.EdgesGeometry(geometry, 35), new THREE.LineBasicMaterial({color: 0xf5f6eb, transparent: true, opacity: 0.85}));
      edge.position.y = 0.002; geography.add(edge); regionCount++;
    }
    const dots = [];
    for (const record of city.businesses || []) {
      if (!Array.isArray(record) || !record.slice(0,3).every(Number.isFinite) || record[2] <= 0) continue;
      const [x,z] = projectPoint(record, city.center);
      if (x < extent.minX || x > extent.maxX || z < extent.minZ || z > extent.maxZ) continue;
      dots.push(x, plateHeight + 0.009, z);
    }
    if (dots.length) {
      const pointGeometry = new THREE.BufferGeometry(); pointGeometry.setAttribute('position', new THREE.Float32BufferAttribute(dots,3));
      businessCloud = new THREE.Points(pointGeometry, new THREE.PointsMaterial({color:0x204d40,size:0.025,sizeAttenuation:true,transparent:true,opacity:0.72,depthWrite:false}));
      businessCloud.name='baseline-reviewed-businesses'; businessCloud.renderOrder=2; geography.add(businessCloud);
    }
    for (const project of (city.projects || []).slice(0,9)) {
      if (!Array.isArray(project.center) || !project.center.every(Number.isFinite)) continue;
      const [x,z] = projectPoint(project.center,city.center);
      if (x < extent.minX || x > extent.maxX || z < extent.minZ || z > extent.maxZ) continue;
      const canvas = document.createElement('canvas'); canvas.width=512; canvas.height=96;
      const ctx=canvas.getContext('2d'); ctx.fillStyle='#f5f2e5'; ctx.fillRect(0,0,512,96);
      ctx.strokeStyle='#386451';ctx.lineWidth=3;ctx.strokeRect(2,2,508,92);
      ctx.fillStyle='#204a3b';ctx.font='bold 46px sans-serif';ctx.textAlign='center';ctx.textBaseline='middle';
      ctx.fillText(String(project.name||project.label||'Documented project').slice(0,36),256,48,482);
      const texture=new THREE.CanvasTexture(canvas);texture.colorSpace=THREE.SRGBColorSpace;
      const label=new THREE.Mesh(new THREE.PlaneGeometry(1,96/512),new THREE.MeshStandardMaterial({map:texture,roughness:1,side:THREE.DoubleSide}));
      label.userData.coordinates=project.center.slice(0,2);
      label.position.set(x,plateHeight+0.24,z);label.name='landmark-'+String(project.name||project.label||'project');label.renderOrder=3;
      landmarks.add(label);landmarkLabels.push(label);
      const dot=new THREE.Mesh(new THREE.CylinderGeometry(0.028,0.028,0.02,12),new THREE.MeshStandardMaterial({color:0x265b48,roughness:1}));
      dot.position.set(x,plateHeight+0.016,z);landmarks.add(dot);
    }
    pickPlane = new THREE.Mesh(new THREE.PlaneGeometry(width, depth), new THREE.MeshBasicMaterial({transparent: true, opacity: 0, depthWrite: false, side: THREE.DoubleSide}));
    pickPlane.name = 'interaction-surface'; pickPlane.rotation.x = -Math.PI / 2;
    pickPlane.position.set(boardMid.x, plateHeight + 0.003, boardMid.z); geography.add(pickPlane);
    const north = new THREE.Mesh(new THREE.ConeGeometry(boardSpan * 0.01, boardSpan * 0.04, 3), new THREE.MeshStandardMaterial({color: 0x265b4b, roughness: 1}));
    north.rotation.x = -Math.PI / 2; north.position.set(extent.maxX - boardSpan * 0.04, plateHeight + 0.012, extent.minZ + boardSpan * 0.045); north.name = 'north-arrow'; geography.add(north);
    updateLabel(); resetCamera();
    report('city', `${city.label || city.id}: ${regionCount} real ZIP boundaries. Heights are schematic; click a location to select a 500 m catchment.`, {city: city.id});
    return true;
  }
  function setSelection(value) {
    if (!city || !value || !Number.isFinite(value.longitude) || !Number.isFinite(value.latitude)) return false;
    selection = {...value, radiusMeters: Math.max(1, Number(value.radiusMeters) || 500)}; release(marker);
    const [x, z] = projectPoint([selection.longitude, selection.latitude], city.center), r = selection.radiusMeters / 1000;
    const ring = new THREE.Mesh(new THREE.RingGeometry(r * 0.97, r * 1.03, 96).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({color: 0xcc7434, roughness: 0.8, side: THREE.DoubleSide}));
    ring.position.set(x, plateHeight + 0.025, z); marker.add(ring);
    const disc = new THREE.Mesh(new THREE.CircleGeometry(r, 96).rotateX(-Math.PI / 2),
      new THREE.MeshStandardMaterial({color: 0xedb277, transparent: true, opacity: 0.23, depthWrite: false, side: THREE.DoubleSide}));
    disc.position.set(x, plateHeight + 0.02, z); marker.add(disc);
    const stemHeight = Math.max(0.16, Math.min(0.4, boardSpan * 0.01));
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.015, 0.015, stemHeight, 12), new THREE.MeshStandardMaterial({color: 0x994721, roughness: 0.8}));
    stem.position.set(x, plateHeight + stemHeight / 2, z); marker.add(stem);
    const pin = new THREE.Mesh(new THREE.SphereGeometry(Math.max(0.04, Math.min(0.08, boardSpan * 0.002)), 20, 12), new THREE.MeshStandardMaterial({color: 0xe3954a, roughness: 0.55}));
    pin.position.set(x, plateHeight + stemHeight, z); marker.add(pin);
    updateLabel(); return true;
  }
  function focusSelection() {
    if (!selection || !city) return false;
    const [x,z] = projectPoint([selection.longitude, selection.latitude], city.center);
    const span = Math.max(1.6, selection.radiusMeters / 1000 * 5);
    controls.target.set(x, plateHeight, z);
    camera.position.set(x + span * 0.18, span * 0.88, z + span * 0.94);
    controls.minDistance = 0.12; controls.update(); return true;
  }
  function acceptIntersection() {
    if (!pickPlane || !city) return;
    map.updateWorldMatrix(true, true);
    const landmarkHit = raycaster.intersectObjects(landmarkLabels, false)[0];
    if (landmarkHit) {
      const [longitude,latitude] = landmarkHit.object.userData.coordinates;
      const value = {longitude,latitude,radiusMeters:500,cityId:city.id};onPick(value);return;
    }
    const hit = raycaster.intersectObject(pickPlane)[0]; if (!hit) return;
    const local = map.worldToLocal(hit.point.clone());
    const [longitude, latitude] = unprojectPoint([local.x, local.z], city.center);
    const value = {longitude, latitude, radiusMeters: 500, cityId: city.id}; onPick(value);
  }
  function pointerDown(event) { if (event.button === 0) pointerStart = {x: event.clientX, y: event.clientY}; }
  function pointerUp(event) {
    const start = pointerStart; pointerStart = null;
    if (!start || Math.hypot(event.clientX - start.x, event.clientY - start.y) > 6) return;
    const rect = renderer.domElement.getBoundingClientRect();
    pointer.set((event.clientX - rect.left) / rect.width * 2 - 1, -(event.clientY - rect.top) / rect.height * 2 + 1);
    raycaster.setFromCamera(pointer, camera); acceptIntersection();
  }
  renderer.domElement.addEventListener('pointerdown', pointerDown);
  renderer.domElement.addEventListener('pointerup', pointerUp);
  renderer.domElement.addEventListener('pointercancel', () => { pointerStart = null; });
  renderer.setAnimationLoop(() => {
    if (disposed) return;
    controls.update();
    const viewer = camera;
    const viewQuaternion = viewer.getWorldQuaternion(new THREE.Quaternion());
    const localQuaternion = map.getWorldQuaternion(new THREE.Quaternion()).invert().multiply(viewQuaternion);
    for (const label of landmarkLabels) {
      label.quaternion.copy(localQuaternion);
      const distance = camera.position.distanceTo(label.position);
      label.scale.setScalar(Math.min(2.0,Math.max(0.65,distance*0.23)));
    }
    renderer.render(scene, camera);
  });
  report('ready', '3D map ready. Choose a location within 500 m of reviewed businesses.');
  return {setCity, setSelection, setMetrics(value = {}) {metrics = {...value}; updateLabel();},
    reset: resetCamera, focusSelection, getCapabilities: () => ({...capabilities}),
    async dispose() {
      disposed = true; observer.disconnect(); renderer.setAnimationLoop(null);
      renderer.domElement.removeEventListener('pointerdown', pointerDown); renderer.domElement.removeEventListener('pointerup', pointerUp);
      controls.dispose(); release(map);
      renderer.dispose(); renderer.domElement.remove();
    }};
}
