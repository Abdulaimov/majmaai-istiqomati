// Stills of the running site at full resolution, from the named views of main.js or from given cameras.
//
//   npx vite --port 5196 &
//   node tools/mi/shots.mjs build/shots [--size 1600x1000] [--hours 10.5] [--ui] \
//        name|"label:sx,sy,h:tx,ty,th[:fov]" ...      (site metres: x east, y north, h height)
import { chromium } from 'playwright-core';
import { mkdirSync } from 'node:fs';

const args = process.argv.slice(2);
const opt = (k, d) => (args.includes(`--${k}`) ? args[args.indexOf(`--${k}`) + 1] : d);
const flags = new Set(['--ui']);
const pos = args.filter((a, i) => !a.startsWith('--') && !(args[i - 1]?.startsWith('--') && !flags.has(args[i - 1])));
const out = pos[0] ?? 'build/shots';
const shots = pos.slice(1);
const url = opt('url', 'http://localhost:5196/');
const [W, H] = opt('size', '1600x1000').split('x').map(Number);
const hours = opt('hours', null);
mkdirSync(out, { recursive: true });
const browser = await chromium.launch({
  executablePath: process.env.CHROME ?? `${process.env.HOME}/Library/Caches/ms-playwright/chromium-1223/chrome-mac-arm64/Google Chrome for Testing.app/Contents/MacOS/Google Chrome for Testing`,
  headless: true,
  args: ['--use-angle=metal', '--enable-gpu', '--ignore-gpu-blocklist'],
});
const page = await browser.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
page.on('console', (m) => (m.type() === 'error' || m.type() === 'warning') && console.log('console:', m.text()));
page.on('pageerror', (e) => console.log('pageerror:', e.message));
const t0 = Date.now();
await page.goto(`${url}?still`);
await page.waitForFunction(() => window.__app?.building && window.__app?.hqDone, null, { timeout: 180000 });
console.log(`loaded in ${Date.now() - t0} ms`);
await page.waitForTimeout(2500);
for (const s of shots) {
  const name = await page.evaluate(async ({ s, hours, ui }) => {
    const app = window.__app;
    app.setClean(!ui);
    if (hours != null) app.setHours(+hours);
    let name = s;
    // the client renders' cameras (fitted to the vanishing points and corners of block К: render 10
    // from across the inner street, render 9 from the south-east); level, with the shift of a
    // two-point perspective: the full frame centred on the horizon, the render's part of it shown
    // (tools/mi/fitcam.py: least squares on 7 and 5 corners, rms 7 and 5 px of 4940)
    const RENDER = {
      r10: { pos: [117.95, 5.43, 5.79], fwd: [-0.9832, 0.1824], f: 3991.7, cx: 2185.2, cy: 2960.7, w: 4940, h: 3493 },
      r9: { pos: [133.92, -50.24, 7.4], fwd: [-0.9686, 0.2486], f: 3922.3, cx: 2499.3, cy: 2877.4, w: 4940, h: 3493 },
    };
    app.camera.clearViewOffset();
    if (RENDER[s]) {
      const r = RENDER[s];
      const [x, y, h] = r.pos;
      app.controls.maxPolarAngle = Math.PI * 0.6;
      app.setView([x, h, -y], [x + r.fwd[0] * 100, h, -(y + r.fwd[1] * 100)]);
      // the full frame centred on the principal point, the render's part of it shown
      const A = Math.max(r.cx, r.w - r.cx), B = Math.max(r.cy, r.h - r.cy);
      app.camera.fov = (2 * Math.atan(B / r.f) * 180) / Math.PI;
      app.camera.aspect = A / B;
      app.camera.setViewOffset(2 * A, 2 * B, A - r.cx, B - r.cy, r.w, r.h);
      app.camera.updateProjectionMatrix();
      app.shadowsDirty();
      await new Promise((res) => setTimeout(res, 1800));
      return name;
    }
    if (s.startsWith('block=')) {
      const v = app.blockView(s.slice(6));
      app.select(s.slice(6));
      app.setView(v.pos.toArray(), v.target.toArray());
      app.camera.fov = 32;
      app.camera.updateProjectionMatrix();
      await new Promise((res) => setTimeout(res, 1800));
      return s.replace('=', '_');
    }
    if (s.includes(':')) {
      const [label, a, b, fov] = s.split(':');
      const [x, y, h] = a.split(',').map(Number), [tx, ty, th] = b.split(',').map(Number);
      app.camera.fov = fov ? +fov : 32;
      app.camera.updateProjectionMatrix();
      app.setView([x, h, -y], [tx, th, -ty]);
      name = label;
    } else {
      app.camera.fov = 32;
      app.camera.updateProjectionMatrix();
      app.view(s);
    }
    app.shadowsDirty();
    await new Promise((r) => setTimeout(r, 1800));
    return name;
  }, { s, hours, ui: args.includes('--ui') });
  await page.screenshot({ path: `${out}/${name}.png` });
  console.log('saved', `${out}/${name}.png`);
}
const info = await page.evaluate(() => {
  const r = window.__app.renderer.info.render;
  return { triangles: r.triangles, calls: r.calls };
});
console.log(info);
await browser.close();
