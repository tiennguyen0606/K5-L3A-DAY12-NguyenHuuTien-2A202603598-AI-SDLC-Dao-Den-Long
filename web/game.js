import * as THREE from './vendor/three.module.js';
import {
  DEFAULT_BINDINGS, DEFAULT_SENSITIVITY, DEFAULT_VOLUME,
  clampSensitivity, clampVolume, duplicateBindings, nextMouseYaw,
} from './controls.mjs';

const $ = selector => document.querySelector(selector);
const canvas = $('#game'), menu = $('#menu'), hud = $('#hud'), pauseView = $('#pause'), resultView = $('#result');
const palette = {
  sky: 0x0e1430, fog: 0x1b2350, grass: 0x2f5d50, sand: 0xc9b48a, wood: 0x6b4a2f, cloud: 0x12384a,
  amber: 0xffb347, core: 0xffe9b0, off: 0x5b5f6e, mote: 0xfff6c2, shade: 0x120a1a, shadeEdge: 0x7a3cff,
  cloth: 0xe8e2d0, red: 0xc8102e, drifter: 0x8fa3b8,
};
const layouts = {
  1: { name: 'ĐẢO BẾN', duration: 240, lanterns: [[0, 25], [23.8, 7.7], [14.7, -20.2], [-14.7, -20.2], [-23.8, 7.7]] },
  2: { name: 'ĐẢO CAU', duration: 270, lanterns: [[0, 20], [17, -10], [-17, -10], [70, 20], [87, -10], [53, -10]] },
  3: { name: 'ĐẢO CHUÔNG', duration: 300, lanterns: [[0, 6], [18, 10], [-18, 10], [35, -10], [-35, -10], [20, -35], [-20, -35]] },
};

let renderer, scene, camera, world, player, clock = new THREE.Clock();
let currentNight = 1, running = false, paused = false, lastWon = false, yaw = 0;
let score = 0, totalScore = 0, nightsWon = 0, currentSeed = 42, timeLeft = 240;
let carried = 0, flames = 3, successfulLights = 0, pulseCd = 0, dashCd = 0, dashTime = 0;
let yVelocity = 0, jumpRequested = false, lastFacing = new THREE.Vector3(0, 0, 1);
let lanterns = [], motes = [], shades = [], keys = new Set(), nextShadeIndex = 3, shadeSpawnTimer = 5;
let windTimer = 30, windActive = 0, windWarn = 0, windDir = new THREE.Vector3(1, 0, 0);
let audioCtx = null, musicGain = null, musicOsc = null;
let mouseSensitivity = clampSensitivity(localStorage.getItem('mouseSensitivity') || DEFAULT_SENSITIVITY);
let masterVolume = clampVolume(localStorage.getItem('masterVolume') || DEFAULT_VOLUME);
const distinctColors = () => $('#distinct-colors').checked;
const reducedMotion = () => $('#reduced-motion').checked;
function loadBindings() {
  try { return { ...DEFAULT_BINDINGS, ...JSON.parse(localStorage.getItem('bindings') || '{}') }; }
  catch { return { ...DEFAULT_BINDINGS }; }
}
let bindings = loadBindings();

try {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
} catch (error) {
  $('#webgl-error').hidden = false;
  throw error;
}
scene = new THREE.Scene();
scene.background = new THREE.Color(palette.sky);
scene.fog = new THREE.FogExp2(palette.fog, 0.012);
camera = new THREE.PerspectiveCamera(58, innerWidth / innerHeight, 0.1, 500);

const mat = (color, extra = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.8, ...extra });
function mesh(geometry, material, position = [0, 0, 0]) {
  const item = new THREE.Mesh(geometry, material);
  item.position.set(...position);
  item.castShadow = true;
  item.receiveShadow = true;
  return item;
}
function cylinder(radius, depth, color, position, segments = 48) {
  return mesh(new THREE.CylinderGeometry(radius, radius, depth, segments), mat(color), position);
}

function ensureAudio() {
  if (audioCtx) return;
  audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  musicGain = audioCtx.createGain();
  musicGain.gain.value = masterVolume * 0.08;
  musicGain.connect(audioCtx.destination);
  musicOsc = audioCtx.createOscillator();
  musicOsc.type = 'sine';
  musicOsc.frequency.value = 110;
  musicOsc.connect(musicGain);
  musicOsc.start();
}

function setVolume(value) {
  masterVolume = clampVolume(value);
  localStorage.setItem('masterVolume', String(masterVolume));
  if (musicGain) musicGain.gain.value = masterVolume * 0.08;
}

function playTone(freq, duration = 0.12, type = 'triangle', gain = 0.08) {
  if (masterVolume <= 0.001) return;
  ensureAudio();
  const osc = audioCtx.createOscillator();
  const g = audioCtx.createGain();
  osc.type = type;
  osc.frequency.value = freq;
  g.gain.value = masterVolume * gain;
  osc.connect(g);
  g.connect(audioCtx.destination);
  const now = audioCtx.currentTime;
  g.gain.exponentialRampToValueAtTime(0.0001, now + duration);
  osc.start(now);
  osc.stop(now + duration);
}

function setupAtmosphere() {
  scene.add(new THREE.HemisphereLight(0x53659d, 0x09101f, 1.65));
  const moon = new THREE.DirectionalLight(0x9eaeff, 2.2);
  moon.position.set(-24, 45, -18);
  moon.castShadow = true;
  moon.shadow.mapSize.set(2048, 2048);
  moon.shadow.camera.left = -70;
  moon.shadow.camera.right = 70;
  moon.shadow.camera.top = 70;
  moon.shadow.camera.bottom = -70;
  scene.add(moon);
  const stars = new THREE.BufferGeometry(), positions = [];
  for (let i = 0; i < 650; i++) {
    const a = Math.random() * Math.PI * 2, r = 90 + Math.random() * 100, y = 25 + Math.random() * 80;
    positions.push(Math.cos(a) * r, y, Math.sin(a) * r);
  }
  stars.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
  scene.add(new THREE.Points(stars, new THREE.PointsMaterial({ color: 0xdde5ff, size: 0.38, sizeAttenuation: true })));
  scene.add(mesh(new THREE.SphereGeometry(5, 32, 16), new THREE.MeshBasicMaterial({ color: 0xfff3d0 }), [-55, 58, -90]));
}
setupAtmosphere();

function islandDisc(x, z, r, height = 1, y = -0.5, color = palette.grass) {
  const group = new THREE.Group();
  group.add(cylinder(r, height, color, [x, y, z]));
  const rim = cylinder(r + 1.2, 0.25, palette.sand, [x, y - height / 2 + 0.08, z]);
  rim.material.roughness = 1;
  group.add(rim);
  return group;
}
function addTree(x, z, s = 1) {
  const tree = new THREE.Group();
  tree.add(cylinder(0.18 * s, 2.2 * s, palette.wood, [0, 1.1 * s, 0], 10));
  tree.add(mesh(new THREE.ConeGeometry(1.2 * s, 2.8 * s, 8), mat(0x244f48), [0, 3 * s, 0]));
  tree.position.set(x, 0, z);
  world.add(tree);
}
function addBridge() {
  for (let x = 27; x <= 43; x += 1.1) {
    const plank = mesh(new THREE.BoxGeometry(1, 0.28, 4), mat(palette.wood), [x, 0.08, 0]);
    plank.rotation.y = (Math.random() - 0.5) * 0.04;
    world.add(plank);
  }
  for (const z of [-2.1, 2.1]) {
    const rope = mesh(new THREE.CylinderGeometry(0.055, 0.055, 18, 8), mat(0x3f2d20), [35, 1.3, z]);
    rope.rotation.z = Math.PI / 2;
    world.add(rope);
  }
}
function buildTerrain() {
  if (currentNight === 1) world.add(islandDisc(0, 0, 40));
  if (currentNight === 2) { world.add(islandDisc(0, 0, 28), islandDisc(70, 0, 28)); addBridge(); }
  if (currentNight === 3) {
    world.add(islandDisc(0, 0, 45));
    world.add(cylinder(24, 3, palette.grass, [0, 1.5, 3]));
    world.add(cylinder(8, 3, palette.grass, [0, 4.5, 0]));
    world.add(cylinder(2, 8, palette.wood, [0, 10, 0], 18));
  }
  const centres = currentNight === 2 ? [0, 70] : [0];
  for (const centre of centres) {
    for (let i = 0; i < 18; i++) {
      const a = i / 18 * Math.PI * 2 + 0.2, r = 14 + (i % 4) * 4;
      if (currentNight !== 3 || r > 24) addTree(centre + Math.cos(a) * r, Math.sin(a) * r, 0.65 + (i % 3) * 0.12);
    }
  }
}
function buildPlayer() {
  const group = new THREE.Group();
  group.add(mesh(new THREE.CapsuleGeometry(0.48, 1.05, 5, 10), mat(palette.cloth), [0, 1.15, 0]));
  const scarf = mesh(new THREE.BoxGeometry(0.18, 0.8, 0.12), mat(palette.red), [0.42, 1.25, 0.12]);
  scarf.rotation.z = -0.32;
  group.add(scarf);
  group.add(mesh(new THREE.ConeGeometry(1.05, 0.42, 24), mat(palette.sand), [0, 2.05, 0]));
  group.add(mesh(new THREE.SphereGeometry(0.18, 12, 8), mat(palette.amber, { emissive: palette.amber, emissiveIntensity: 3 }), [-0.48, 1.15, 0.18]));
  const light = new THREE.PointLight(palette.amber, 4, 9, 2);
  light.position.set(-0.48, 1.2, 0.18);
  group.add(light);
  group.position.set(0, 0.1, 0);
  world.add(group);
  return group;
}
function buildLantern(id, x, z) {
  const group = new THREE.Group();
  group.userData = { id, deposited: 0, lit: false, fuel: 0, everLit: false, relitCount: 0 };
  group.add(cylinder(0.16, 2.5, palette.wood, [0, 1.25, 0], 10));
  const frame = mesh(new THREE.CylinderGeometry(0.42, 0.34, 0.86, 8), mat(palette.off, { emissive: palette.off, emissiveIntensity: 0.08 }), [0, 2.35, 0]);
  frame.name = 'lamp';
  group.add(frame);
  group.add(mesh(new THREE.ConeGeometry(0.64, 0.38, 8), mat(palette.wood), [0, 2.94, 0]));
  const light = new THREE.PointLight(palette.amber, 0, 12, 2);
  light.position.y = 2.4;
  light.name = 'light';
  group.add(light);
  const fuelBack = mesh(new THREE.BoxGeometry(1.25, 0.12, 0.08), new THREE.MeshBasicMaterial({ color: 0x141827 }), [0, 3.35, 0]);
  fuelBack.name = 'fuel-back';
  fuelBack.visible = false;
  group.add(fuelBack);
  const fuelFill = mesh(new THREE.BoxGeometry(1.18, 0.07, 0.1), new THREE.MeshBasicMaterial({ color: palette.amber }), [0, 3.35, 0.02]);
  fuelFill.name = 'fuel-fill';
  fuelFill.visible = false;
  group.add(fuelFill);
  group.position.set(x, 0, z);
  world.add(group);
  return group;
}
function makeMote(x, z, index) {
  const group = new THREE.Group();
  group.userData = { id: `M${index}`, phase: index * 0.7 };
  group.add(mesh(new THREE.SphereGeometry(0.15, 10, 8), new THREE.MeshBasicMaterial({ color: palette.mote }), [0, 0.8, 0]));
  const light = new THREE.PointLight(0xffe58a, 0.8, 3, 2);
  light.position.y = 0.8;
  group.add(light);
  group.position.set(x, 0, z);
  world.add(group);
  return group;
}
function makeShade(x, z, index) {
  const edge = distinctColors() ? 0x00b3ff : palette.shadeEdge;
  const group = new THREE.Group();
  group.userData = { id: `S${index}`, stun: 0, state: 'wander', alert: 2.5 };
  group.add(mesh(new THREE.CapsuleGeometry(0.55, 1.1, 4, 9), mat(palette.shade, { emissive: edge, emissiveIntensity: 0.16 }), [0, 1, 0]));
  group.add(mesh(new THREE.SphereGeometry(0.1, 8, 6), new THREE.MeshBasicMaterial({ color: edge }), [-0.2, 1.25, 0.5]));
  group.position.set(x, 0, z);
  world.add(group);
  playTone(90, 0.25, 'sawtooth', 0.05);
  return group;
}
function populate() {
  lanterns = layouts[currentNight].lanterns.map((p, i) => buildLantern(`L${i + 1}`, p[0], p[1]));
  const centres = currentNight === 2 ? [0, 70] : [0];
  motes = [];
  for (let i = 0; i < 20; i++) {
    const centre = centres[i % centres.length], a = i * 0.91, r = 8 + (i % 4) * 5;
    motes.push(makeMote(centre + Math.cos(a) * r, Math.sin(a) * r, i + 1));
  }
  shades = [
    makeShade(currentNight === 2 ? 24 : 30, 15, 1),
    makeShade(currentNight === 2 ? 78 : -28, currentNight === 2 ? -17 : -17, 2),
  ];
  nextShadeIndex = 3;
  shadeSpawnTimer = 5;
  windTimer = 30;
  windActive = 0;
  windWarn = 0;
}
function clearWorld() {
  if (world) scene.remove(world);
  world = new THREE.Group();
  scene.add(world);
}
function resetGame() {
  clearWorld();
  buildTerrain();
  player = buildPlayer();
  populate();
  score = 0;
  carried = 0;
  flames = 3;
  successfulLights = 0;
  timeLeft = layouts[currentNight].duration;
  pulseCd = 0;
  dashCd = 0;
  dashTime = 0;
  yVelocity = 0;
  jumpRequested = false;
  paused = false;
  yaw = 0;
  lastFacing.set(0, 0, 1);
  updateHud();
}
function lightLantern(lantern) {
  const relight = lantern.userData.everLit;
  lantern.userData.lit = true;
  lantern.userData.fuel = 100;
  lantern.userData.everLit = true;
  lantern.userData.relitCount += relight ? 1 : 0;
  successfulLights++;
  const lamp = lantern.getObjectByName('lamp');
  lamp.scale.y = 1;
  lamp.material = mat(palette.amber, { emissive: palette.amber, emissiveIntensity: 2 });
  lantern.getObjectByName('light').intensity = 5;
  score += relight ? 40 : 100;
  let ring = lantern.getObjectByName('safe-ring');
  if (!ring) {
    ring = mesh(new THREE.RingGeometry(5.85, 6, 64), new THREE.MeshBasicMaterial({ color: palette.amber, transparent: true, opacity: 0.35, side: THREE.DoubleSide }), [0, 0.03, 0]);
    ring.rotation.x = -Math.PI / 2;
    ring.name = 'safe-ring';
    lantern.add(ring);
  }
  ring.visible = true;
  playTone(520, 0.18, 'sine', 0.07);
}
function extinguishLantern(lantern) {
  lantern.userData.lit = false;
  lantern.userData.fuel = 0;
  lantern.userData.deposited = 0;
  const lamp = lantern.getObjectByName('lamp');
  lamp.scale.y = 0.8;
  lamp.material = mat(palette.off);
  lantern.getObjectByName('light').intensity = 0;
  const ring = lantern.getObjectByName('safe-ring');
  if (ring) ring.visible = false;
}
function interact() {
  if (!running || paused || carried === 0) return;
  const nearby = lanterns
    .filter(l => flatDistance(l.position, player.position) <= 2 && (!l.userData.lit || l.userData.fuel < 100))
    .sort((a, b) => flatDistance(a.position, player.position) - flatDistance(b.position, player.position) || a.userData.id.localeCompare(b.userData.id))[0];
  if (!nearby) return;
  if (nearby.userData.lit) {
    const amount = Math.min(carried, Math.ceil((100 - nearby.userData.fuel) / 10));
    nearby.userData.fuel = Math.min(100, nearby.userData.fuel + amount * 10);
    carried -= amount;
    score += amount * 5;
    playTone(340, 0.1);
    updateHud();
    return;
  }
  const cost = nearby.userData.everLit ? 5 : 10;
  const amount = Math.min(carried, cost - nearby.userData.deposited);
  nearby.userData.deposited += amount;
  carried -= amount;
  score += amount * 5;
  if (nearby.userData.deposited === cost) lightLantern(nearby);
  else playTone(300, 0.08);
  updateHud();
}
function pulse() {
  if (!running || paused || carried < 3 || pulseCd > 0) return;
  carried -= 3;
  pulseCd = 3;
  playTone(220, 0.2, 'square', 0.06);
  for (const shade of shades) {
    if (flatDistance(shade.position, player.position) <= 5) {
      score += shade.userData.state === 'drain' ? 15 : 5;
      shade.userData.stun = 2;
      shade.userData.state = 'stunned';
      const away = shade.position.clone().sub(player.position).setY(0).normalize();
      shade.position.addScaledVector(away, 4);
    }
  }
  if (!reducedMotion()) {
    const wave = mesh(new THREE.RingGeometry(0.8, 1.05, 48), new THREE.MeshBasicMaterial({ color: palette.core, transparent: true, opacity: 0.9, side: THREE.DoubleSide }), [player.position.x, 0.12, player.position.z]);
    wave.rotation.x = -Math.PI / 2;
    scene.add(wave);
    let age = 0;
    const grow = () => {
      age += 0.04;
      wave.scale.setScalar(1 + age * 4);
      wave.material.opacity = 1 - age;
      if (age < 1) requestAnimationFrame(grow);
      else scene.remove(wave);
    };
    grow();
  }
  updateHud();
}
function flatDistance(a, b) { return Math.hypot(a.x - b.x, a.z - b.z); }
function capacity() { return Math.min(20, 10 + 2 * successfulLights); }
function groundAt(x, z) {
  if (currentNight === 1) return Math.hypot(x, z) <= 40 ? 0 : null;
  if (currentNight === 2) return (Math.hypot(x, z) <= 28 || Math.hypot(x - 70, z) <= 28 || (x >= 26 && x <= 44 && Math.abs(z) <= 2.2)) ? 0 : null;
  const r = Math.hypot(x, z);
  if (r <= 8) return 6;
  if (r >= 12 && r <= 24 && z > 0) return 3;
  return r <= 45 ? 0 : null;
}
function projectEdgeMarker(worldPos, element) {
  const vector = worldPos.clone().project(camera);
  const onScreen = vector.z < 1 && Math.abs(vector.x) <= 1 && Math.abs(vector.y) <= 1;
  if (onScreen) {
    element.hidden = true;
    return;
  }
  const angle = Math.atan2(vector.y, vector.x);
  const x = Math.cos(angle) * 0.42 + 0.5;
  const y = -Math.sin(angle) * 0.38 + 0.5;
  element.hidden = false;
  element.style.left = `${x * 100}%`;
  element.style.top = `${y * 100}%`;
  element.style.transform = `translate(-50%, -50%) rotate(${-angle}rad)`;
}
function updateAlerts() {
  const shadeAlert = $('#shade-alert');
  const windAlert = $('#wind-alert');
  const countdownAlert = $('#countdown-alert');
  const fuelAlert = $('#fuel-alert');
  const lanternArrow = $('#lantern-arrow');
  const marked = shades.find(s => s.userData.alert > 0);
  if (marked) projectEdgeMarker(marked.position.clone().setY(1.2), shadeAlert);
  else shadeAlert.hidden = true;
  windAlert.hidden = !(windWarn > 0 || windActive > 0);
  windAlert.textContent = windWarn > 0 ? `${distinctColors() ? '⚠ ' : ''}Gió sắp thổi` : `${distinctColors() ? '⚠ ' : ''}Gió đang kéo`;
  const seconds = Math.max(0, Math.ceil(timeLeft));
  countdownAlert.hidden = !(running && seconds <= 10 && seconds > 0);
  countdownAlert.textContent = `${distinctColors() ? '⚠ ' : ''}${seconds}s tới bình minh`;
  const lowFuel = lanterns.some(l => l.userData.lit && l.userData.fuel < 30);
  fuelAlert.hidden = !lowFuel;
  fuelAlert.textContent = `${distinctColors() ? '⚠ ' : ''}Đèn sắp hết dầu`;
  const target = lanterns
    .filter(l => !l.userData.lit)
    .sort((a, b) => flatDistance(a.position, player.position) - flatDistance(b.position, player.position) || a.userData.id.localeCompare(b.userData.id))[0];
  if (target) projectEdgeMarker(target.position.clone().setY(2.4), lanternArrow);
  else lanternArrow.hidden = true;
}
function updatePlayer(dt) {
  const forward = new THREE.Vector3(Math.sin(yaw), 0, Math.cos(yaw));
  const right = new THREE.Vector3(-forward.z, 0, forward.x);
  const move = new THREE.Vector3();
  if (keys.has(bindings.forward)) move.add(forward);
  if (keys.has(bindings.backward)) move.sub(forward);
  if (keys.has(bindings.right)) move.add(right);
  if (keys.has(bindings.left)) move.sub(right);
  if (move.lengthSq() > 0) {
    move.normalize();
    lastFacing.copy(move);
    player.rotation.y = Math.atan2(move.x, move.z);
  }
  const speed = dashTime > 0 ? 14 : 6;
  player.position.addScaledVector(dashTime > 0 ? lastFacing : move, speed * dt);
  if (windActive > 0) player.position.addScaledVector(windDir, 2 * dt);
  const ground = groundAt(player.position.x, player.position.z);
  const grounded = ground !== null && player.position.y <= ground + 0.12 && yVelocity <= 0;
  if (jumpRequested && grounded) {
    yVelocity = 7;
    playTone(180, 0.08, 'square', 0.04);
  }
  jumpRequested = false;
  if (!grounded || yVelocity > 0) {
    yVelocity -= 20 * dt;
    player.position.y += yVelocity * dt;
  } else if (ground !== null) {
    player.position.y = ground + 0.1;
    yVelocity = 0;
  }
  if (ground === null && player.position.y < -10) {
    flames--;
    carried = 0;
    yVelocity = 0;
    player.position.set(0, 0.1, 0);
    playTone(70, 0.3, 'sawtooth', 0.06);
    if (flames <= 0) finish(false);
  }
}
function updateEntities(dt, elapsed) {
  shadeSpawnTimer -= dt;
  if (shadeSpawnTimer <= 0 && shades.length < (currentNight === 1 ? 6 : currentNight === 2 ? 8 : 10)) {
    const angle = Math.random() * Math.PI * 2;
    const radius = currentNight === 2 ? 26 : currentNight === 3 ? 43 : 37;
    const cx = currentNight === 2 && Math.random() > 0.5 ? 70 : 0;
    shades.push(makeShade(cx + Math.cos(angle) * radius, Math.sin(angle) * radius, nextShadeIndex++));
    shadeSpawnTimer = currentNight === 1 ? 8 : currentNight === 2 ? 7 : 6;
  }
  if (currentNight === 3) {
    if (windActive > 0) windActive = Math.max(0, windActive - dt);
    else if (windWarn > 0) {
      windWarn = Math.max(0, windWarn - dt);
      if (windWarn === 0) windActive = 5;
    } else {
      windTimer -= dt;
      if (windTimer <= 0) {
        windWarn = 2;
        windTimer = 30;
        const angle = Math.random() * Math.PI * 2;
        windDir.set(Math.cos(angle), 0, Math.sin(angle));
        playTone(140, 0.4, 'sine', 0.05);
      }
    }
  }
  for (const mote of [...motes]) {
    mote.position.y = Math.sin(elapsed * 2 + mote.userData.phase) * 0.2;
    mote.rotation.y += dt;
    if (carried < capacity() && flatDistance(mote.position, player.position) <= 1) {
      carried++;
      world.remove(mote);
      motes.splice(motes.indexOf(mote), 1);
      playTone(660, 0.07, 'sine', 0.05);
    }
  }
  for (const lantern of lanterns) {
    if (lantern.userData.lit) {
      lantern.userData.fuel = Math.max(0, lantern.userData.fuel - dt);
      if (lantern.userData.fuel <= 0) extinguishLantern(lantern);
    }
    const low = lantern.userData.lit && lantern.userData.fuel < 30;
    const fill = lantern.getObjectByName('fuel-fill');
    const back = lantern.getObjectByName('fuel-back');
    fill.visible = back.visible = lantern.userData.lit;
    if (fill.visible) {
      fill.scale.x = Math.max(0.001, lantern.userData.fuel / 100);
      fill.position.x = -0.59 * (1 - fill.scale.x);
      fill.material.color.setHex(low ? (distinctColors() ? 0xffffff : 0xff5a5f) : palette.amber);
      fill.visible = !low || Math.floor(elapsed * 2) % 2 === 0;
    }
    const ring = lantern.getObjectByName('safe-ring');
    if (ring) ring.visible = lantern.userData.lit && lantern.userData.fuel >= 30;
  }
  for (const shade of shades) {
    shade.userData.alert = Math.max(0, shade.userData.alert - dt);
    if (shade.userData.stun > 0) {
      shade.userData.stun -= dt;
      shade.children[0].material.emissive.setHex(0x3a3450);
      continue;
    }
    shade.children[0].material.emissive.setHex(distinctColors() ? 0x00b3ff : palette.shadeEdge);
    const weak = lanterns
      .filter(l => l.userData.lit && l.userData.fuel < 30)
      .sort((a, b) => flatDistance(a.position, shade.position) - flatDistance(b.position, shade.position) || a.userData.id.localeCompare(b.userData.id));
    if (weak.length) {
      const target = weak[0], d = flatDistance(shade.position, target.position);
      if (d <= 2) {
        shade.userData.state = 'drain';
        target.userData.fuel = Math.max(0, target.userData.fuel - 5 * dt);
        continue;
      }
      const dir = target.position.clone().sub(shade.position).setY(0).normalize();
      shade.position.addScaledVector(dir, 4 * dt);
      shade.rotation.y = Math.atan2(dir.x, dir.z);
      continue;
    }
    shade.userData.state = 'chase';
    const d = flatDistance(shade.position, player.position);
    if (d < 18 && d > 1) {
      const dir = player.position.clone().sub(shade.position).setY(0).normalize();
      shade.position.addScaledVector(dir, 4 * dt);
      shade.rotation.y = Math.atan2(dir.x, dir.z);
    }
    if (d <= 1 && flames > 0) {
      flames--;
      carried = Math.floor(carried / 2);
      playTone(80, 0.25, 'sawtooth', 0.07);
      if (!reducedMotion()) document.body.classList.add('hit-flash');
      setTimeout(() => document.body.classList.remove('hit-flash'), 120);
      if (flames <= 0) finish(false);
    }
  }
}
function updateCamera(dt) {
  const target = player.position.clone().add(new THREE.Vector3(0, 1.3, 0));
  const offset = new THREE.Vector3(-Math.sin(yaw) * 8, 5.2, -Math.cos(yaw) * 8);
  const blend = reducedMotion() ? 1 : 1 - Math.pow(0.002, dt);
  camera.position.lerp(target.clone().add(offset), blend);
  camera.lookAt(target);
}
function updateHud() {
  $('#flames').innerHTML = Array.from({ length: flames }, () => '<i class="flame"></i>').join('');
  const total = lanterns.length || layouts[currentNight].lanterns.length;
  const lit = lanterns.filter(l => l.userData.lit).length;
  $('#lantern-count').textContent = `ĐÈN ${lit} / ${total}`;
  $('#score').textContent = String(score).padStart(4, '0');
  $('#night-name').textContent = layouts[currentNight].name;
  const seconds = Math.max(0, Math.ceil(timeLeft));
  const timer = $('#timer');
  timer.textContent = `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  timer.classList.toggle('urgent', seconds <= 30);
  $('#danger-text').textContent = seconds <= 30 ? `${distinctColors() ? '⚠ ' : ''}BÌNH MINH ĐANG TỚI` : '';
  $('#motes').innerHTML = Array.from({ length: capacity() }, (_, i) => `<i class="mote ${i < carried ? 'full' : ''}"></i>`).join('');
  $('#motes').setAttribute('aria-label', `${carried} trên ${capacity()} đom đóm`);
  $('#dash-cd').classList.toggle('cooling', dashCd > 0);
  $('#pulse-cd').classList.toggle('cooling', pulseCd > 0);
  const near = lanterns
    .filter(l => flatDistance(l.position, player.position) <= 2 && (!l.userData.lit || l.userData.fuel < 100))
    .sort((a, b) => flatDistance(a.position, player.position) - flatDistance(b.position, player.position))[0];
  $('#prompt').textContent = near
    ? (near.userData.lit
      ? `E  ·  CHÂM DẦU  ${near.userData.fuel.toFixed(0)}/100`
      : `E  ·  ${near.userData.everLit ? 'THẮP LẠI' : 'NẠP ÁNH SÁNG'}  ${near.userData.deposited}/${near.userData.everLit ? 5 : 10}`)
    : '';
  updateAlerts();
}
function setPause(value) {
  if (!running) return;
  paused = value;
  pauseView.hidden = !value;
  if (value) {
    document.exitPointerLock?.();
    $('#resume').focus();
  } else canvas.requestPointerLock?.();
}
function finish(won) {
  lastWon = won;
  if (won) {
    for (const lantern of lanterns.filter(l => l.userData.lit)) score += 50 + Math.floor(lantern.userData.fuel);
    score += flames * 50;
    totalScore += score;
    nightsWon++;
    playTone(440, 0.35, 'sine', 0.08);
  } else playTone(95, 0.45, 'sawtooth', 0.08);
  running = false;
  document.exitPointerLock?.();
  resultView.hidden = false;
  $('#result-kicker').textContent = won ? 'ÁNH SÁNG ĐÃ TRỞ LẠI' : 'SƯƠNG ĐEN THẮNG THẾ';
  $('#result-title').textContent = won ? 'Bình minh trên đảo' : 'Ngọn đèn đã tắt';
  $('#result-copy').textContent = won ? 'Mây đã giữ đủ ánh sáng tới bình minh.' : 'Chưa đủ đèn sáng khi bình minh tới.';
  $('#result-score').textContent = totalScore;
  $('#result-action').textContent = won && currentNight < 3 ? 'Đi tới đêm kế tiếp' : 'Chơi lại đêm';
  $('#score-form').hidden = false;
  $('#score-form').querySelector('button').disabled = false;
  $('#score-message').textContent = '';
  $('#result-action').focus();
  updateAlerts();
}
function frame() {
  requestAnimationFrame(frame);
  const dt = Math.min(clock.getDelta(), 0.05);
  const elapsed = clock.elapsedTime;
  if (running && !paused) {
    dashTime = Math.max(0, dashTime - dt);
    dashCd = Math.max(0, dashCd - dt);
    pulseCd = Math.max(0, pulseCd - dt);
    timeLeft = Math.max(0, timeLeft - dt);
    updatePlayer(dt);
    updateEntities(dt, elapsed);
    if (flames <= 0) finish(false);
    else if (timeLeft <= 0) finish(lanterns.filter(l => l.userData.lit).length >= Math.ceil(lanterns.length * 0.6));
    updateHud();
  } else if (running) updateAlerts();
  if (player) updateCamera(dt);
  renderer.render(scene, camera);
}

addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  camera.updateProjectionMatrix();
  renderer.setSize(innerWidth, innerHeight, false);
});
renderer.setSize(innerWidth, innerHeight, false);
addEventListener('keydown', event => {
  const key = event.key.toLowerCase();
  keys.add(key);
  if ([bindings.forward, bindings.backward, bindings.left, bindings.right].includes(key) && running && !paused && document.pointerLockElement !== canvas) {
    canvas.requestPointerLock?.();
  }
  if (key === bindings.jump) jumpRequested = true;
  if (key === bindings.interact) interact();
  if (key === bindings.pulse) pulse();
  if (key === bindings.dash && dashCd <= 0 && running && !paused) {
    dashTime = 0.2;
    dashCd = 1.5;
    playTone(250, 0.08, 'triangle', 0.04);
  }
  if ((key === bindings.pause || key === 'escape') && running) setPause(!paused);
  if (key === 'r' && running) resetGame();
});
addEventListener('keyup', event => keys.delete(event.key.toLowerCase()));
addEventListener('mousemove', event => {
  yaw = nextMouseYaw(yaw, event.movementX, {
    running, paused, pointerLocked: document.pointerLockElement === canvas, pointerOnCanvas: event.target === canvas, pressedKeys: keys,
  }, mouseSensitivity);
});
canvas.addEventListener('pointerdown', event => {
  if (running && !paused) {
    event.preventDefault();
    ensureAudio();
    canvas.requestPointerLock?.().catch?.(() => {});
  }
});
addEventListener('blur', () => keys.clear());
$('#start').addEventListener('click', () => {
  ensureAudio();
  currentNight = Number($('#night').value);
  totalScore = 0;
  nightsWon = 0;
  menu.hidden = true;
  hud.hidden = false;
  resultView.hidden = true;
  resetGame();
  running = true;
  clock.getDelta();
  canvas.requestPointerLock?.();
});
$('#resume').addEventListener('click', () => setPause(false));
$('#restart').addEventListener('click', () => {
  pauseView.hidden = true;
  resetGame();
  running = true;
  canvas.requestPointerLock?.();
});
$('#back-menu').addEventListener('click', () => location.reload());
$('#result-action').addEventListener('click', () => {
  if (lastWon && currentNight < 3) currentNight++;
  resultView.hidden = true;
  resetGame();
  running = true;
  canvas.requestPointerLock?.();
});
$('#result-menu').addEventListener('click', () => location.reload());
$('#score-form').addEventListener('submit', async event => {
  event.preventDefault();
  const name = $('#player-name').value.trim();
  try {
    const response = await fetch('/api/leaderboard', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name, score: totalScore, nights_won: nightsWon, achieved_at: new Date().toISOString(), seed: currentSeed,
      }),
    });
    const value = await response.json();
    if (!response.ok) throw new Error(value.error || 'Không lưu được');
    $('#score-message').textContent = 'Đã lưu thành tích.';
    $('#score-form').querySelector('button').disabled = true;
  } catch (error) {
    $('#score-message').textContent = error.message;
  }
});
async function showLeaderboard() {
  const list = $('#leaderboard-list');
  list.replaceChildren();
  try {
    const response = await fetch('/api/leaderboard');
    const { entries } = await response.json();
    for (const [index, entry] of entries.entries()) {
      const row = document.createElement('li');
      const rank = document.createElement('span');
      const name = document.createElement('span');
      const points = document.createElement('strong');
      rank.textContent = `${index + 1}.`;
      name.textContent = entry.name;
      points.textContent = String(entry.score);
      row.append(rank, name, points);
      list.append(row);
    }
    if (!entries.length) {
      const empty = document.createElement('li');
      empty.textContent = 'Chưa có thành tích';
      list.append(empty);
    }
  } catch {
    const error = document.createElement('li');
    error.textContent = 'Không tải được bảng xếp hạng';
    list.append(error);
  }
  $('#leaderboard').hidden = false;
  $('#close-leaderboard').focus();
}
$('#show-leaderboard').addEventListener('click', showLeaderboard);
$('#close-leaderboard').addEventListener('click', () => {
  $('#leaderboard').hidden = true;
  $('#show-leaderboard').focus();
});
const actionLabels = {
  forward: 'Tiến', backward: 'Lùi', left: 'Trái', right: 'Phải', jump: 'Nhảy',
  dash: 'Lướt', interact: 'Tương tác', pulse: 'Tỏa sáng', pause: 'Tạm dừng',
};
function renderBindings() {
  const grid = $('#binding-grid');
  grid.replaceChildren();
  for (const [action, labelText] of Object.entries(actionLabels)) {
    const label = document.createElement('label');
    const text = document.createElement('span');
    const input = document.createElement('input');
    text.textContent = labelText;
    input.readOnly = true;
    input.dataset.action = action;
    input.value = bindings[action] === ' ' ? 'Space' : bindings[action];
    input.addEventListener('keydown', event => {
      event.preventDefault();
      const key = event.key.toLowerCase();
      bindings = { ...bindings, [action]: key };
      input.value = key === ' ' ? 'Space' : key;
      const duplicates = duplicateBindings(bindings);
      $('#binding-error').textContent = duplicates.length
        ? `Trùng phím: ${duplicates.map(item => actionLabels[item]).join(', ')}`
        : '';
    });
    label.append(text, input);
    grid.append(label);
  }
}
function applyAccessibility() {
  document.body.classList.toggle('reduced-motion', $('#reduced-motion').checked);
  document.body.classList.toggle('large-ui', $('#large-ui').checked);
  localStorage.setItem('reducedMotion', String($('#reduced-motion').checked));
  localStorage.setItem('largeUi', String($('#large-ui').checked));
}
function syncSettingsForm() {
  $('#volume').value = String(masterVolume);
  $('#volume-value').textContent = `${Math.round(masterVolume * 100)}%`;
  $('#sensitivity').value = String(mouseSensitivity);
  $('#sensitivity-value').textContent = mouseSensitivity.toFixed(4);
}
$('#show-settings').addEventListener('click', () => {
  bindings = loadBindings();
  renderBindings();
  syncSettingsForm();
  $('#binding-error').textContent = '';
  $('#settings').hidden = false;
  $('#close-settings').focus();
});
$('#close-settings').addEventListener('click', () => {
  $('#settings').hidden = true;
  $('#show-settings').focus();
});
$('#reset-bindings').addEventListener('click', () => {
  bindings = { ...DEFAULT_BINDINGS };
  mouseSensitivity = DEFAULT_SENSITIVITY;
  setVolume(DEFAULT_VOLUME);
  renderBindings();
  syncSettingsForm();
  $('#binding-error').textContent = '';
});
$('#volume').addEventListener('input', event => {
  setVolume(event.target.value);
  $('#volume-value').textContent = `${Math.round(masterVolume * 100)}%`;
});
$('#sensitivity').addEventListener('input', event => {
  mouseSensitivity = clampSensitivity(event.target.value);
  $('#sensitivity-value').textContent = mouseSensitivity.toFixed(4);
});
$('#save-settings').addEventListener('click', () => {
  const duplicates = duplicateBindings(bindings);
  if (duplicates.length) {
    $('#binding-error').textContent = 'Hãy xử lý các phím bị trùng.';
    return;
  }
  localStorage.setItem('bindings', JSON.stringify(bindings));
  localStorage.setItem('mouseSensitivity', String(mouseSensitivity));
  setVolume(masterVolume);
  applyAccessibility();
  $('#settings').hidden = true;
  $('#show-settings').focus();
});
$('#distinct-colors').checked = localStorage.getItem('distinctColors') === 'true';
$('#distinct-colors').addEventListener('change', () => {
  localStorage.setItem('distinctColors', String(distinctColors()));
  document.documentElement.style.setProperty('--danger', distinctColors() ? '#ffffff' : '#ff5a5f');
});
$('#reduced-motion').checked = localStorage.getItem('reducedMotion') === 'true';
$('#large-ui').checked = localStorage.getItem('largeUi') === 'true';
applyAccessibility();
syncSettingsForm();
currentNight = 1;
resetGame();
camera.position.set(0, 7, -10);
frame();
if (new URLSearchParams(location.search).has('autostart')) $('#start').click();
