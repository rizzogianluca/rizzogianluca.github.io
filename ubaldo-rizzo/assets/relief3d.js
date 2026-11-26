// Interactive 3D view of the chapel relief (Cappella), built from a photographic
// albedo and an estimated height map. Three.js is loaded from the import map in the page.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const box = document.getElementById('r3d');
const msg = box.querySelector('.r3d-msg');
const base = box.dataset.base;

function fail() {
  box.classList.add('r3d-fallback');
  msg.hidden = true;
}

let renderer;
try {
  renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
} catch (e) { fail(); throw e; }

renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
renderer.toneMapping = THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure = 1.05;
box.prepend(renderer.domElement);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x14110e);
const camera = new THREE.PerspectiveCamera(38, 1, 0.02, 50);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true;
controls.dampingFactor = 0.07;
controls.minDistance = 0.35;
controls.maxDistance = 12;

const key = new THREE.DirectionalLight(0xfff1e0, 2.3);
const fill = new THREE.DirectionalLight(0xd6e0f0, 0.5);
fill.position.set(-2, -1, 2);
scene.add(key, fill, new THREE.AmbientLight(0x7a7468, 0.45));

const $ = (id) => document.getElementById(id);
let aspect = 5.75, mat, albedo;

// camera presets: whole panel and the three catalogued sections
const VIEWS = { intero: [0.5, 0], superiore: [0.83, 1.35], centrale: [0.5, 1.35], inferiore: [0.17, 1.35] };
let tween = null;
function go(name, instant) {
  const v = VIEWS[name] || VIEWS.intero;
  const y = (v[0] - 0.5) * aspect;
  const t = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2));
  const dist = v[1] ? Math.max(v[1], 0.62 / (t * camera.aspect)) : Math.max((aspect / 2) * 1.06 / t, 0.6 / (t * camera.aspect));
  const toT = new THREE.Vector3(0, y, 0.03), toP = new THREE.Vector3(name === 'intero' ? 0.6 : 0.3, y, dist);
  document.querySelectorAll('[data-view]').forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.view === name)));
  if (instant || matchMedia('(prefers-reduced-motion: reduce)').matches) {
    controls.target.copy(toT); camera.position.copy(toP); return;
  }
  tween = { t: 0, fT: controls.target.clone(), fP: camera.position.clone(), toT, toP };
}

function light() {
  const az = THREE.MathUtils.degToRad(+$('r3d-az').value);
  const el = THREE.MathUtils.degToRad(+$('r3d-el').value);
  key.position.set(4 * Math.cos(el) * Math.sin(az), 4 * Math.sin(el), 4 * Math.cos(el) * Math.cos(az));
}
$('r3d-az').addEventListener('input', light);
$('r3d-el').addEventListener('input', light);
light();

function size() {
  const w = box.clientWidth, h = box.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
}
new ResizeObserver(size).observe(box);
size();

const loader = new THREE.TextureLoader();
Promise.all([loader.loadAsync(base + 'cappella-albedo.jpg'), loader.loadAsync(base + 'cappella-height.png')]).then(([alb, height]) => {
  albedo = alb;
  alb.colorSpace = THREE.SRGBColorSpace;
  const an = renderer.capabilities.getMaxAnisotropy();
  alb.anisotropy = an; height.anisotropy = an;
  aspect = alb.image.height / alb.image.width;
  const segX = 360, segY = Math.round(segX * aspect);
  mat = new THREE.MeshStandardMaterial({ map: alb, displacementMap: height, displacementScale: +$('r3d-depth').value, roughness: 0.74, metalness: 0.02 });
  const relief = new THREE.Mesh(new THREE.PlaneGeometry(1, aspect, segX, segY), mat);
  scene.add(relief);
  const slab = new THREE.Mesh(new THREE.BoxGeometry(1.05, aspect + 0.05, 0.09), new THREE.MeshStandardMaterial({ color: 0xcdc6ba, roughness: 0.7 }));
  slab.position.z = -0.046;
  scene.add(slab);
  msg.hidden = true;
  box.classList.add('r3d-ready');

  $('r3d-depth').addEventListener('input', (e) => { mat.displacementScale = +e.target.value; });
  document.querySelectorAll('[data-mat]').forEach((b) => b.addEventListener('click', () => {
    const plaster = b.dataset.mat === 'gesso';
    mat.map = plaster ? null : albedo;
    mat.color.set(plaster ? 0xe2dccf : 0xffffff);
    mat.needsUpdate = true;
    document.querySelectorAll('[data-mat]').forEach((x) => x.setAttribute('aria-pressed', String(x === b)));
  }));

  // double-click / double-tap: orbit around that point
  const ray = new THREE.Raycaster(), p = new THREE.Vector2();
  renderer.domElement.addEventListener('dblclick', (ev) => {
    const r = renderer.domElement.getBoundingClientRect();
    p.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
    ray.setFromCamera(p, camera);
    const hit = ray.intersectObject(relief)[0];
    if (hit) tween = { t: 0, fT: controls.target.clone(), fP: camera.position.clone(), toT: hit.point.clone(), toP: camera.position.clone() };
  });

  go((location.hash || '#intero').slice(1), true);
}).catch(fail);

document.querySelectorAll('[data-view]').forEach((b) => b.addEventListener('click', () => {
  history.replaceState(null, '', '#' + b.dataset.view);
  go(b.dataset.view);
}));
addEventListener('hashchange', () => go(location.hash.slice(1)));

renderer.setAnimationLoop(() => {
  if (tween) {
    tween.t = Math.min(1, tween.t + 0.04);
    const k = 1 - Math.pow(1 - tween.t, 3);
    controls.target.lerpVectors(tween.fT, tween.toT, k);
    camera.position.lerpVectors(tween.fP, tween.toP, k);
    if (tween.t >= 1) tween = null;
  }
  controls.update();
  renderer.render(scene, camera);
});
