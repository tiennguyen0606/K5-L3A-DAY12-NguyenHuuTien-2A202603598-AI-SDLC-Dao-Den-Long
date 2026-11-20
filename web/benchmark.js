import * as THREE from './vendor/three.module.js';

function mulberry32(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), 1 | t);
    r ^= r + Math.imul(r ^ (r >>> 7), 61 | r);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

const params = new URLSearchParams(location.search);
const started = performance.now();
const duration = Math.max(1, Number(params.get('duration') || 30));
const seed = Number(params.get('seed') || 42);
const rng = mulberry32(seed);

const canvas = document.querySelector('#bench');
const renderer = new THREE.WebGLRenderer({
  canvas,
  antialias: false,
  powerPreference: 'high-performance',
  alpha: false,
});
renderer.setSize(1280, 720, false);
renderer.setPixelRatio(1);
renderer.shadowMap.enabled = false;
renderer.setAnimationLoop(loop);

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0e1430);
scene.fog = new THREE.Fog(0x1b2350, 40, 110);
const camera = new THREE.PerspectiveCamera(58, 1280 / 720, 0.1, 200);

scene.add(new THREE.AmbientLight(0x53659d, 1.2));
scene.add(new THREE.HemisphereLight(0x9eaeff, 0x09101f, 0.9));
for (const [x, z] of [[0, 25], [23.8, 7.7], [-23.8, 7.7]]) {
  const light = new THREE.PointLight(0xffb347, 3.5, 16, 2);
  light.position.set(x, 3, z);
  scene.add(light);
}

const ground = new THREE.Mesh(
  new THREE.CylinderGeometry(40, 40, 1, 32),
  new THREE.MeshLambertMaterial({ color: 0x2f5d50 }),
);
ground.position.y = -0.5;
scene.add(ground);

const dummy = new THREE.Object3D();
const shadeGeometry = new THREE.CapsuleGeometry(0.4, 0.9, 2, 5);
const shadeMaterial = new THREE.MeshLambertMaterial({
  color: 0x120a1a,
  emissive: 0x7a3cff,
  emissiveIntensity: 0.12,
});
const shadeMesh = new THREE.InstancedMesh(shadeGeometry, shadeMaterial, 200);
const shadePhases = [];
const shadeRadii = [];
for (let i = 0; i < 200; i++) {
  const angle = rng() * Math.PI * 2;
  const radius = 6 + rng() * 30;
  shadePhases.push(angle);
  shadeRadii.push(radius);
  dummy.position.set(Math.cos(angle) * radius, 1, Math.sin(angle) * radius);
  dummy.updateMatrix();
  shadeMesh.setMatrixAt(i, dummy.matrix);
}
shadeMesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
scene.add(shadeMesh);

const moteGeometry = new THREE.SphereGeometry(0.12, 5, 4);
const moteMaterial = new THREE.MeshBasicMaterial({ color: 0xfff6c2 });
const moteMesh = new THREE.InstancedMesh(moteGeometry, moteMaterial, 100);
for (let i = 0; i < 100; i++) {
  const angle = rng() * Math.PI * 2;
  const radius = 5 + rng() * 28;
  dummy.position.set(Math.cos(angle) * radius, 0.8, Math.sin(angle) * radius);
  dummy.updateMatrix();
  moteMesh.setMatrixAt(i, dummy.matrix);
}
scene.add(moteMesh);

const lanternMaterial = new THREE.MeshLambertMaterial({
  color: 0xffb347,
  emissive: 0xffb347,
  emissiveIntensity: 1.4,
});
for (const [x, z] of [[0, 25], [23.8, 7.7], [-23.8, 7.7]]) {
  const item = new THREE.Mesh(new THREE.CylinderGeometry(0.38, 0.32, 0.85, 6), lanternMaterial);
  item.position.set(x, 2.4, z);
  scene.add(item);
}

const player = new THREE.Mesh(
  new THREE.CapsuleGeometry(0.4, 0.9, 2, 6),
  new THREE.MeshLambertMaterial({ color: 0xe8e2d0 }),
);
player.position.set(0, 1, 0);
scene.add(player);

let firstFrame = null;
let lastFrame = null;
let measureStarted = null;
const frameTimes = [];

function percentile(values, p) {
  const sorted = [...values].sort((a, b) => a - b);
  return sorted[Math.max(0, Math.ceil(p * sorted.length) - 1)];
}

function finish() {
  const count = frameTimes.length;
  const worstCount = Math.max(1, Math.ceil(0.01 * count));
  const worst = [...frameTimes].sort((a, b) => b - a).slice(0, worstCount);
  window.benchmarkResult = {
    contract_version: '1.3',
    avg_fps: 1000 * count / frameTimes.reduce((a, b) => a + b, 0),
    p1_low_fps: 1000 / (worst.reduce((a, b) => a + b, 0) / worst.length),
    frame_ms_p95: percentile(frameTimes, 0.95),
    frames: count,
    load_ms: firstFrame - started,
    peak_mem_mb: null,
    vsync_off: true,
    renderer: `Three.js r181 / ${renderer.capabilities.isWebGL2 ? 'WebGL2' : 'WebGL1'} / ${renderer.info.render.calls} calls`,
    os: navigator.userAgent,
  };
  renderer.setAnimationLoop(null);
  document.body.dataset.complete = 'true';
}

function loop(now) {
  if (firstFrame === null) firstFrame = now;
  const elapsed = (now - firstFrame) / 1000;
  if (elapsed >= 3 && measureStarted === null) {
    measureStarted = now;
    lastFrame = now;
  }
  if (measureStarted !== null) {
    if (now > lastFrame) frameTimes.push(now - lastFrame);
    lastFrame = now;
    if ((now - measureStarted) / 1000 >= duration) {
      finish();
      return;
    }
  }
  const t = now / 1000;
  for (let i = 0; i < 200; i++) {
    shadePhases[i] += 0.004;
    dummy.position.set(
      Math.cos(shadePhases[i]) * shadeRadii[i],
      1,
      Math.sin(shadePhases[i]) * shadeRadii[i],
    );
    dummy.updateMatrix();
    shadeMesh.setMatrixAt(i, dummy.matrix);
  }
  shadeMesh.instanceMatrix.needsUpdate = true;
  // Clockwise from above would be negative angle; contract wants CCW from +X.
  const angle = -t * Math.PI * 2 / 15;
  camera.position.set(Math.cos(angle) * 30, 15, Math.sin(angle) * 30);
  camera.lookAt(0, 0, 0);
  renderer.render(scene, camera);
}
