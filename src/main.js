// The complex in 3D, outside: turn it, come close, pick a block, watch it from morning to night.
// Block К is built in full; the other blocks stand as white models of their size on their places
// until they are made (blender/build_mi.py). Interiors and flats come in the next stage.
import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { LAMPS, ORDER, PLACES, TOWERS, toScene, towerByKey } from './config.js';
import { buildWorld } from './world.js';
import { OUTLINE, loadComplex } from './building.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { DAY, FIRST, LAST, clock as hhmm, timeOfDay } from './night.js';
import { captureAt } from './reflections.js';
import { Q, setQuality } from './quality.js';
import { createRenderer, createPipeline } from './render.js';
import { setupMaterial, water } from './materials.js';
import { WIND, updateCars } from './props.js';
import { L, getLang, setLang } from './i18n.js';

const $ = (s) => document.querySelector(s);
const touch = matchMedia('(pointer: coarse)').matches;

// ---------- wording ----------
function applyStatic() {
  document.querySelectorAll('[data-t]').forEach((el) => {
    const v = L()[el.dataset.t];
    if (typeof v === 'string') el.textContent = v;
  });
  document.querySelectorAll('.lang button').forEach((b) => b.classList.toggle('on', b.dataset.lang === getLang()));
  $('#daytime-range').setAttribute('aria-label', L().dayTime);
  $('#daytime').title = L().dayTime;
  const eye = $('#eye'), clean = document.body.classList.contains('clean');
  eye.title = clean ? L().showUi : L().hideUi;
  eye.setAttribute('aria-label', eye.title);
  const q = $('#quality');
  q.textContent = L().quality(Q.level === 'high');
  q.title = L().qualityTitle(Q.level === 'high');
  $('#hint').textContent = touch ? L().hintTouch : L().hint;
  document.title = `${L().brand} — 3D`;
}
applyStatic();
document.querySelector('.lang').addEventListener('click', (e) => {
  const b = e.target.closest('button[data-lang]');
  if (!b || b.dataset.lang === getLang()) return;
  setLang(b.dataset.lang);
  applyStatic();
  buildLabels();
  render();
});

// ---------- renderer / scene ----------
let renderer;
try {
  renderer = createRenderer();
} catch (err) {
  console.error(err);
  $('#loading').hidden = true;
  $('#nogl').hidden = false;
  throw err;
}
$('#stage').appendChild(renderer.domElement);
const canvas = renderer.domElement;
canvas.addEventListener('webglcontextlost', (e) => {
  e.preventDefault();
  $('#nogl').hidden = false;
  $('#nogl .why').textContent = L().contextLost;
});

const scene = new THREE.Scene();
renderer.shadowMap.autoUpdate = false;
let shadowFrames = 2;
const shadowsDirty = () => (shadowFrames = 2);
THREE.DefaultLoadingManager.onProgress = shadowsDirty;

const camera = new THREE.PerspectiveCamera(32, innerWidth / innerHeight, 1, 30000);
const P = (x, y, h) => {
  const s = toScene(x, y);
  return new THREE.Vector3(s.x, h, s.z);
};
// views (site metres): block К from across the inner street (render 10), from above the corner
// (render 4), from the corner of the streets, its crown; the whole complex from the south-east
const VIEWS = {
  home: { pos: P(150, 22, 24), target: P(2, 2, 35) },
  homeTall: { pos: P(215, 26, 36), target: P(0, 0, 33) },
  street: { pos: P(132, 70, 2.5), target: P(0, 0, 33) },
  corner: { pos: P(150, -40, 2.5), target: P(6, -6, 31) },
  air: { pos: P(170, -150, 150), target: P(-10, 10, 20) },
  top: { pos: P(55, -40, 105), target: P(0, 0, 62) },
  complex: { pos: P(260, -210, 330), target: P(-70, 110, 0) },
};
const home = () => (innerWidth < innerHeight ? VIEWS.homeTall : VIEWS.home);
camera.position.copy(home().pos);

const controls = new OrbitControls(camera, canvas);
controls.target.copy(home().target);
controls.enableDamping = true;
controls.dampingFactor = 0.08;
controls.minDistance = 8;
controls.maxDistance = 1100;
// (a little above the horizon too: from the street the tower is seen looking up, as on the renders;
// the camera is kept over the ground in the loop)
controls.maxPolarAngle = Math.PI * 0.56;
controls.autoRotateSpeed = 0.25;
controls.update();

let building = null;
const loadingEl = $('#loading');
const modelLoad = loadComplex([], renderer, (k) => (loadingEl.querySelector('b').textContent = `${Math.round(k * 100)}%`));
const world = buildWorld(scene, renderer, modelLoad.then(() => {}, () => {}));
const pipeline = createPipeline(renderer, scene, camera);

// invisible prisms over every block, for hovering and clicking a block
const picks = [];
const marks = {};
for (const t of TOWERS) {
  const shape = new THREE.Shape((t.podium ?? t.outline).map(([x, y]) => {
    const w = toScene(x, y);
    return new THREE.Vector2(w.x, -w.z);
  }));
  const g = new THREE.ExtrudeGeometry(shape, { depth: t.top + 2, bevelEnabled: false });
  g.rotateX(-Math.PI / 2);
  const m = new THREE.Mesh(g, new THREE.MeshBasicMaterial({ visible: false }));
  m.userData.block = t.key;
  scene.add(m);
  picks.push(m);
  // the block under the pointer or chosen: a bright outline round its volume and a light fill
  const edges = new LineSegments2(new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(g, 30)), OUTLINE.hover);
  edges.renderOrder = 11;
  edges.visible = false;
  scene.add(edges);
  const fillMat = new THREE.MeshBasicMaterial({ color: 0xffa42b, transparent: true, opacity: 0.16, depthWrite: false,
    polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -4 });   // (over the model's own faces)
  const fill = new THREE.Mesh(g, fillMat);
  fill.renderOrder = 10;
  fill.visible = false;
  scene.add(fill);
  marks[t.key] = { edges, fill };
}
function showMarks() {
  for (const [k, m] of Object.entries(marks)) {
    const on = k === state.hover || (k === state.block && k !== 'K');
    m.edges.visible = on;
    m.edges.material = k === state.block ? OUTLINE.chosen : OUTLINE.hover;
    // (block К is shown as it is: no tint over its facades)
    m.fill.visible = on && k !== 'K';
  }
}

modelLoad
  .then((b) => {
    building = b;
    scene.add(b.group);
    setupMaterial(world.cityMat, renderer);
    shadowsDirty();
    loadingEl.hidden = true;
    render();
  })
  .catch((err) => {
    console.error(err);
    loadingEl.textContent = L().loadFailed;
  });

$('#quality').onclick = () => setQuality(Q.level === 'high' ? 'low' : 'high');

// ---------- time of day (src/night.js) ----------
let daytime = null;
const dtRange = $('#daytime-range'), dtClock = $('#daytime-clock');
dtRange.min = FIRST;
dtRange.max = LAST;
dtRange.step = 0.25;
dtRange.value = DAY;
function showHours(h) {
  dtClock.textContent = hhmm(h);
  const s = daytime?.state;
  $('#daytime').dataset.phase = !s ? 'day' : s.night > 0.5 ? 'night' : s.lights > 0.05 || h > 17.5 ? 'dusk' : 'day';
  dtRange.style.setProperty('--k', `${((h - FIRST) / (LAST - FIRST)) * 100}%`);
}
function setHours(h) {
  if (!daytime) return;
  daytime.set(h);
  dtRange.value = daytime.hours;
  showHours(daytime.hours);
}
showHours(DAY);
let hqDone = false;
Promise.all([modelLoad, world.ready])
  .then(() => {
    daytime = timeOfDay({
      scene, camera, renderer, world, lamps: LAMPS, shops: [], toScene, cityLights: world.cityLights,
      changed: (s) => {
        pipeline.bloom(s.lights * 1.15);
        shadowsDirty();
      },
    });
    $('#daytime').hidden = false;
    frameView();
    setHours(DAY);
    if (Q.level === 'high') return highQuality();
  })
  .catch((e) => console.warn('time of day', e))
  .finally(() => (hqDone = true));
dtRange.addEventListener('input', () => setHours(+dtRange.value));
dtRange.addEventListener('pointerup', () => dtRange.blur());

// High quality (computers): the glass reflects its surroundings (taken once, in daylight)
async function highQuality() {
  await new Promise((r) => setTimeout(r, 300));
  const hours = daytime.hours;
  if (hours !== DAY) daytime.set(DAY);
  const k = towerByKey.K;
  captureAt({ renderer, scene, at: P(k.centre[0], k.centre[1], 34), block: 'K' });
  if (hours !== DAY) daytime.set(hours);
  shadowsDirty();
}

// ---------- the eye: hide every panel, only the view stays ----------
function setClean(on) {
  document.body.classList.toggle('clean', on);
  $('#eye').setAttribute('aria-pressed', String(on));
  applyStatic();
  frameView();
}
$('#eye').onclick = () => setClean(!document.body.classList.contains('clean'));

// ---------- state, camera flights ----------
const state = { block: null, hover: null };
let tween = null;
let lastInteraction = performance.now();
function flyTo(v, dur = 1.6) {
  tween = { t: 0, dur, p0: camera.position.clone(), p1: v.pos.clone(), t0: controls.target.clone(), t1: v.target.clone() };
  controls.enabled = false;
}
// the middle of the complex (site metres): a block is seen from its outer side
const MID = TOWERS.reduce((m, t) => [m[0] + t.centre[0] / TOWERS.length, m[1] + t.centre[1] / TOWERS.length], [0, 0]);
const sightRay = new THREE.Raycaster();
function blockView(key) {
  if (key === 'K') return innerWidth < innerHeight ? VIEWS.homeTall : VIEWS.home;
  const t = towerByKey[key];
  const c = P(t.centre[0], t.centre[1], t.top * 0.48);
  // from outside the complex, far enough to see the block whole (its height fills two thirds of
  // the frame), with nothing in between: the directions round it tried from the outward one, the
  // first with a clear line of sight wins
  const out = Math.atan2(-(t.centre[1] - MID[1]), t.centre[0] - MID[0]);
  // (on a narrow screen the block's length decides: it fills 70 % of the frame's width)
  const len = Math.max(...t.outline.map((p) => Math.hypot(p[0] - t.centre[0], p[1] - t.centre[1]))) * 2;
  const tanH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * (innerWidth / innerHeight);
  const r = Math.max(150, t.top * 2.8, len / 2 / (tanH * 0.7));
  const others = picks.filter((m) => m.userData.block !== key);
  for (const h of [t.top * 0.6 + 12, t.top * 1.3 + 30]) {
    for (let k = 0; k < 12; k++) {
      const a = out + (k % 2 ? 1 : -1) * Math.ceil(k / 2) * (Math.PI / 6);
      const pos = new THREE.Vector3(c.x + Math.cos(a) * r, h, c.z + Math.sin(a) * r);
      const d = new THREE.Vector3().subVectors(pos, c);
      sightRay.set(c, d.clone().normalize());
      sightRay.far = d.length();
      if (!sightRay.intersectObjects(others, false).length) return { pos, target: c };
    }
  }
  return { pos: new THREE.Vector3(c.x + Math.cos(out) * r, t.top * 2 + 60, c.z + Math.sin(out) * r), target: c };
}
function select(key) {
  state.block = key;
  showMarks();
  flyTo(key ? blockView(key) : VIEWS.complex);
  render();
}

// ---------- panels ----------
function blockFloors(t) {
  return t.floors_low && t.floors_low !== t.floors ? L().floorsTwo(t.floors_low, t.floors) : L().floorsN(t.floors);
}
function render() {
  const blocks = ORDER.map((k) => towerByKey[k]).filter(Boolean);
  $('#blocks').innerHTML = `
    <button class="overview-btn ${state.block ? '' : 'on'}" data-block="">${L().complex}</button>
    <h3>${L().blocks}</h3>
    ${blocks.map((t) => `
      <button class="block-btn ${t.full ? 'full' : 'model'} ${state.block === t.key ? 'active' : ''} ${state.hover === t.key ? 'hover' : ''}" data-block="${t.key}">
        <span class="num">${t.letter}</span>
        <span class="meta">${blockFloors(t)}<br><i>${t.full ? L().ready : L().soon}</i></span>
      </button>`).join('')}`;
  const t = state.block ? towerByKey[state.block] : null;
  let html;
  if (!t) {
    html = `<h2>${L().introTitle}</h2><p>${L().introText}</p><button class="more-btn" data-more>${L().more}</button>
      <div class="views"><h3>${L().views}</h3>
        <button class="btn" data-view="home">${L().vStreet}</button>
        <button class="btn" data-view="corner">${L().vCorner}</button>
        <button class="btn" data-view="air">${L().vAir}</button>
        <button class="btn" data-view="top">${L().vTop}</button>
      </div>`;
  } else if (t.full) {
    html = `<div class="card-head"><span class="badge">${t.letter}</span><div><h2>${L().kTitle}</h2><div class="sub">${L().partsKa}</div></div></div>
      <ul class="facts"><li>${blockFloors(t)}</li><li>${L().shopsFloors}</li></ul>
      <p>${L().kText}</p><p class="soon">${L().kSoon}</p><button class="more-btn" data-more>${L().more}</button>
      <div class="views"><h3>${L().views}</h3>
        <button class="btn" data-view="street">${L().vStreet}</button>
        <button class="btn" data-view="corner">${L().vCorner}</button>
        <button class="btn" data-view="air">${L().vAir}</button>
        <button class="btn" data-view="top">${L().vTop}</button>
      </div>`;
  } else {
    html = `<div class="card-head"><span class="badge model">${t.letter}</span><div><h2>${L().block(t.letter)}</h2><div class="sub">${blockFloors(t)}</div></div></div>
      <ul class="facts"><li>${L().shopsFloors}</li></ul><p>${L().modelText}</p><button class="more-btn" data-more>${L().more}</button>`;
  }
  $('#card').innerHTML = html;
  $('#card').classList.remove('open');
  updateLabels();
  requestAnimationFrame(frameView);
}
$('#blocks').addEventListener('click', (e) => {
  const b = e.target.closest('[data-block]');
  if (!b) return;
  select(b.dataset.block || null);
});
$('#blocks').addEventListener('pointerover', (e) => {
  const b = e.target.closest('[data-block]');
  setHover(b?.dataset.block || null);
});
$('#blocks').addEventListener('pointerleave', () => setHover(null));
$('#card').addEventListener('click', (e) => {
  if (e.target.closest('[data-more]')) {
    const open = $('#card').classList.toggle('open');
    e.target.textContent = open ? L().less : L().more;
    requestAnimationFrame(frameView);
    return;
  }
  const b = e.target.closest('[data-view]');
  if (b) flyTo(VIEWS[b.dataset.view]);
});

// the 3D view framed in the space the panels leave: the frame's centre moved to the middle between
// the block list and the card (computers), between the time slider and the card (phones)
function frameView() {
  const W = innerWidth, H = innerHeight;
  let dx = 0, dy = 0;
  if (!document.body.classList.contains('clean')) {
    const card = $('#card').getBoundingClientRect();
    if (W > 760) {
      const l = $('#blocks').getBoundingClientRect().right, r = card.left;
      if (r - l > 240) dx = Math.round(W / 2 - (l + r) / 2);
    } else {
      const t = ($('#daytime').hidden ? $('.brand') : $('#daytime')).getBoundingClientRect().bottom, b = card.top;
      if (b - t > 160) dy = Math.round(H / 2 - (t + b) / 2);
    }
  }
  if (dx || dy) camera.setViewOffset(W, H, dx, dy, W, H);
  else camera.clearViewOffset();
  camera.updateProjectionMatrix();
}

// ---------- labels over the blocks ----------
const labelsEl = $('#labels');
let labels = [];
function buildLabels() {
  labelsEl.innerHTML = '';
  labels = [];
  for (const t of TOWERS) {
    const el = document.createElement('button');
    el.className = `tag ${t.full ? 'full' : 'model'}`;
    el.innerHTML = t.full ? `<b>${t.letter}</b><span>${L().ready}</span>` : `<b>${t.letter}</b>`;
    el.onclick = () => select(t.key);
    el.onpointerenter = () => setHover(t.key);
    el.onpointerleave = () => setHover(null);
    labelsEl.appendChild(el);
    const c = toScene(t.centre[0], t.centre[1]);
    labels.push({ el, key: t.key, p: new THREE.Vector3(c.x, t.top + (t.full ? 6 : 4), c.z) });
  }
  for (const p of PLACES) {
    const el = document.createElement('div');
    el.className = 'tag place';
    el.textContent = L()[p.kind] ?? (getLang() === 'tj' ? p.tj : p.ru);
    labelsEl.appendChild(el);
    const c = toScene(p.x, p.y);
    labels.push({ el, p: new THREE.Vector3(c.x, p.z, c.z), place: true });
  }
}
buildLabels();
const v3 = new THREE.Vector3();
// a place's label hides behind a block (a ray to it through the blocks' pick prisms, checked a few
// labels a frame)
const occl = new THREE.Raycaster(), dir3 = new THREE.Vector3();
let occlNext = 0;
function hidden(l, own = null) {
  const d = dir3.subVectors(l.p, camera.position);
  const far = d.length();
  occl.set(camera.position, d.normalize());
  occl.far = far - 2;
  return occl.intersectObjects(picks, false).some((h) => h.object.userData.block !== own);
}
function updateLabels() {
  const W = innerWidth, H = innerHeight;
  const checked = labels.filter((l) => l.place || l.key);
  for (let k = 0; k < 3 && checked.length; k++) {
    const l = checked[occlNext++ % checked.length];
    l.behind = hidden(l, l.key);
  }
  for (const l of labels) {
    v3.copy(l.p).project(camera);
    const vis = v3.z < 1 && Math.abs(v3.x) < 1.1 && Math.abs(v3.y) < 1.1;
    const far = camera.position.distanceTo(l.p);
    // (К's tag always over the whole complex: the way to the block that is ready)
    const shown = l.place ? far < 520 && !l.behind : !l.behind || l.key === state.block || l.key === state.hover || (l.key === 'K' && !state.block);
    l.el.style.display = vis && shown ? '' : 'none';
    if (!vis) continue;
    l.el.style.transform = `translate(${((v3.x + 1) / 2) * W}px, ${((1 - v3.y) / 2) * H}px) translate(-50%, -100%)`;
    l.el.classList.toggle('active', l.key && l.key === state.block);
    l.el.classList.toggle('hover', l.key && l.key === state.hover);
  }
}

// ---------- picking ----------
const ray = new THREE.Raycaster(), ndc = new THREE.Vector2();
function pickAt(e) {
  const r = canvas.getBoundingClientRect();
  ndc.set(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(ndc, camera);
  const hit = ray.intersectObjects(picks, false)[0];
  return hit?.object.userData.block ?? null;
}
function setHover(k) {
  if (state.hover === k) return;
  state.hover = k;
  showMarks();
  canvas.style.cursor = k ? 'pointer' : '';
  document.querySelectorAll('.block-btn').forEach((b) => b.classList.toggle('hover', b.dataset.block === k));
}
let down = null;
canvas.addEventListener('pointerdown', (e) => {
  down = { x: e.clientX, y: e.clientY };
  lastInteraction = performance.now();
});
canvas.addEventListener('pointermove', (e) => {
  if (!down && !touch) setHover(pickAt(e));
});
canvas.addEventListener('pointerup', (e) => {
  if (down && Math.hypot(e.clientX - down.x, e.clientY - down.y) < 6) {
    const k = pickAt(e);
    if (k) select(k);
  }
  down = null;
});
controls.addEventListener('start', () => {
  lastInteraction = performance.now();
  tween = null;
  controls.enabled = true;
});
addEventListener('wheel', () => (lastInteraction = performance.now()), { passive: true });

// ---------- loop ----------
addEventListener('resize', () => {
  camera.aspect = innerWidth / innerHeight;
  frameView();
  pipeline.setSize(innerWidth, innerHeight);
});
const STILL = new URLSearchParams(location.search).has('still');
const clockT = new THREE.Clock();
const ease = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
renderer.info.autoReset = false;
renderer.setAnimationLoop(() => {
  renderer.info.reset();
  const dt = Math.min(clockT.getDelta(), 0.05);
  if (tween) {
    tween.t += dt;
    const k = ease(Math.min(1, tween.t / tween.dur));
    camera.position.lerpVectors(tween.p0, tween.p1, k);
    controls.target.lerpVectors(tween.t0, tween.t1, k);
    camera.lookAt(controls.target);
    if (k >= 1) {
      tween = null;
      controls.enabled = true;
    }
  } else {
    controls.autoRotate = !STILL && performance.now() - lastInteraction > 30000;
    controls.update();
  }
  if (camera.position.y < 1.7) camera.position.y = 1.7;
  updateLabels();
  for (const n of water) n.offset.x += dt * 0.006, n.offset.y += dt * 0.004;
  WIND.t.value += dt;
  updateCars(camera);
  if (shadowFrames > 0) {
    renderer.shadowMap.needsUpdate = true;
    shadowFrames--;
  }
  pipeline.render(dt);
});
render();

// handles for the automated checks in tools/ (screenshots)
window.__app = {
  THREE, scene, camera, controls, renderer, state, pipeline, world, quality: Q, VIEWS,
  get building() { return building; },
  get daytime() { return daytime; },
  get hqDone() { return hqDone; },
  select, flyTo, blockView,
  setHours: (h) => setHours(h),
  setClean: (on) => setClean(on),
  shadowsDirty: () => shadowsDirty(),
  setView(pos, target) {
    tween = null;
    camera.position.set(...pos);
    controls.target.set(...target);
    controls.update();
    shadowsDirty();
  },
  view(name) {
    const v = VIEWS[name];
    this.setView(v.pos.toArray(), v.target.toArray());
  },
};
