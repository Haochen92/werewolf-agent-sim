/**
 * Repeatable rendering census against a separately running production build.
 * Run from frontend/: node scripts/profile-theatre.mjs http://localhost:3137 chromium /tmp/theatre.json
 * Browser may be chromium or webkit. API reads use the bundled nine-seat replay; no game is started.
 * Reports DOM/image inventory, sampled animation bounds, rAF gaps and (Chromium) layer counts/heap.
 * rAF gaps are scheduling observations, NOT presented FPS. RGBA estimates are NOT GPU memory.
 * Linux WebKit is NOT physical iOS Safari. Timing instrumentation itself adds some overhead.
 */
import { chromium, webkit } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';

const [
  base = 'http://localhost:3137',
  engine = 'chromium',
  output = '/tmp/theatre-profile.json',
] = process.argv.slice(2);
if (!['chromium', 'webkit'].includes(engine))
  throw new Error('Browser must be chromium or webkit');
const fixture = JSON.parse(
  readFileSync(
    new URL('../src/stage/fixtures/replay-9369a5c1.json', import.meta.url),
    'utf8',
  ),
);
const browser = await { chromium, webkit }[engine].launch({ headless: true });
const report = {
  engine,
  version: browser.version(),
  base,
  fixture: fixture.game_id,
  generatedAt: new Date().toISOString(),
  samples: [],
  errors: [],
};
try {
  const context = await browser.newContext({
    viewport: { width: 844, height: 390 },
    deviceScaleFactor: 3,
    isMobile: true,
    hasTouch: true,
  });
  await context.route('**/api/**', async (route) => {
    const path = new URL(route.request().url()).pathname;
    const json =
      path === `/api/replays/${fixture.game_id}`
        ? fixture
        : path === '/api/replays'
          ? [fixture]
          : path === '/api/models'
            ? { models: [] }
            : path.endsWith('/ledger') || ['/api/characters', '/api/rooms'].includes(path)
              ? []
              : {};
    await route.fulfill({ json, headers: { 'X-Total-Count': '1' } });
  });
  await context.addInitScript(() => {
    let frames = [],
      tasks = [],
      animations = new Map(),
      running = false,
      last = null;
    const longTasksSupported =
      PerformanceObserver.supportedEntryTypes?.includes('longtask');
    if (longTasksSupported)
      new PerformanceObserver((list) => {
        if (running) tasks.push(...list.getEntries().map((e) => e.duration));
      }).observe({ type: 'longtask' });
    function frame(t) {
      if (running && last !== null) frames.push(t - last);
      last = running ? t : null;
      requestAnimationFrame(frame);
    }
    requestAnimationFrame(frame);
    setInterval(() => {
      if (!running) return;
      for (const a of document.getAnimations()) {
        const el = a.effect?.target;
        if (!el || a.playState !== 'running') continue;
        const r = el.getBoundingClientRect();
        const key = `${el.tagName}.${el.getAttribute('class')}|${el.closest('[data-layer]')?.getAttribute('data-layer')}`;
        const old = animations.get(key);
        if (!old || old.area < r.width * r.height)
          animations.set(key, {
            target: key,
            width: r.width,
            height: r.height,
            area: r.width * r.height,
            duration: a.effect.getTiming().duration,
          });
      }
    }, 100);
    window.__theatreAudit = {
      start() {
        frames = [];
        tasks = [];
        animations = new Map();
        last = null;
        running = true;
      },
      stop() {
        running = false;
        const sorted = [...frames].sort((a, b) => a - b);
        const q = (p) =>
          sorted.length
            ? sorted[Math.min(sorted.length - 1, Math.floor(sorted.length * p))]
            : null;
        return {
          frames: frames.length,
          rafP50Ms: q(0.5),
          rafP95Ms: q(0.95),
          rafMaxMs: q(1),
          gapsOver50Ms: frames.filter((x) => x > 50).length,
          longTasksSupported,
          longTasks: tasks,
          animations: [...animations.values()],
        };
      },
    };
  });
  const page = await context.newPage();
  page.on('pageerror', (e) => report.errors.push(String(e)));
  page.on('crash', () => report.errors.push('Page crashed'));
  let cdp,
    layers = [],
    peakLayers = 0,
    layerUpdates = 0;
  if (engine === 'chromium') {
    cdp = await context.newCDPSession(page);
    await cdp.send('Performance.enable');
    await cdp.send('LayerTree.enable');
    cdp.on('LayerTree.layerTreeDidChange', (e) => {
      layerUpdates++;
      layers = e.layers ?? [];
      peakLayers = Math.max(peakLayers, layers.length);
    });
  }
  async function census(name) {
    const data = await page.evaluate(() => {
      const imgs = [...document.images].map((img) => {
        const r = img.getBoundingClientRect();
        return {
          src: img.currentSrc,
          w: img.naturalWidth,
          h: img.naturalHeight,
          cssW: r.width,
          cssH: r.height,
          rgbaMiB: /\.(webp|png|jpe?g)(\?|$)/.test(img.currentSrc)
            ? (img.naturalWidth * img.naturalHeight * 4) / 1048576
            : 0,
        };
      });
      const unique = [...new Map(imgs.map((i) => [i.src, i])).values()];
      const backdrop = document.querySelector('[data-backdrop] img');
      const mini = document.querySelector('[data-mini]');
      return {
        url: location.href,
        viewport: [innerWidth, innerHeight],
        dpr: devicePixelRatio,
        visibility: document.visibilityState,
        elements: document.querySelectorAll('*').length,
        svgElements: document.querySelectorAll('svg *').length,
        imgElements: imgs.length,
        uniqueImgRgbaMiB: unique.reduce((n, i) => n + i.rgbaMiB, 0),
        images: unique.sort((a, b) => b.rgbaMiB - a.rgbaMiB),
        backdrop: backdrop ? imgs.find((i) => i.src === backdrop.currentSrc) : null,
        mini: mini
          ? {
              top: mini.getBoundingClientRect().top,
              playing: mini.getAttribute('data-playing'),
            }
          : null,
        imageRequests: performance
          .getEntriesByType('resource')
          .filter((e) => /\.(webp|png)/.test(e.name))
          .map((e) => e.name),
        beat: document.querySelector('[data-beat]')?.getAttribute('data-beat'),
        timing: window.__theatreAudit.stop(),
      };
    });
    if (cdp) {
      // Collect only between capture windows, never during timing measurements.
      await cdp.send('HeapProfiler.collectGarbage');
      const { metrics } = await cdp.send('Performance.getMetrics');
      data.chromium = {
        metrics: Object.fromEntries(
          metrics
            .filter((m) => /JSHeapUsedSize|Nodes|Documents|JSEventListeners/.test(m.name))
            .map((m) => [m.name, m.value]),
        ),
        layerUpdatesDuringWindow: layerUpdates,
        // No updates may mean a static scene OR unavailable headless compositing; do not infer a peak.
        settledLayers: layerUpdates ? layers.length : null,
        peakLayers: layerUpdates ? peakLayers : null,
        largestLayers: layerUpdates
          ? layers
              .filter((l) => l.drawsContent)
              .sort((a, b) => b.width * b.height - a.width * a.height)
              .slice(0, 5)
              .map(({ width, height, paintCount }) => ({ width, height, paintCount }))
          : [],
      };
    }
    report.samples.push({ name, ...data });
    writeFileSync(output, JSON.stringify(report, null, 2));
    console.log(
      name,
      data.beat ?? '',
      data.elements,
      'elements',
      data.uniqueImgRgbaMiB.toFixed(1),
      'MiB image estimate',
    );
  }
  async function start() {
    peakLayers = layers.length;
    layerUpdates = 0;
    await page.evaluate(() => window.__theatreAudit.start());
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/`, { waitUntil: 'networkidle' });
  await page.locator('[data-mini]').waitFor({ state: 'attached' });
  await start();
  await page.waitForTimeout(1500);
  await census('landing-before-scroll');
  await page.locator('[data-mini]').scrollIntoViewIfNeeded();
  await start();
  await page.waitForTimeout(4000);
  await census('landing-preview-visible');
  await page.evaluate(() => scrollTo(0, 0));
  await start();
  await page.waitForTimeout(1000);
  await census('landing-after-scroll-away');

  await page.setViewportSize({ width: 844, height: 390 });
  for (const scene of ['day', 'vote', 'pack']) {
    await page.goto(
      `${base}/workbench/${scene}?game=9369a5c1&beat=0&animate=1&frame=iphone14&hud=replay`,
      { waitUntil: 'networkidle' },
    );
    await page.waitForTimeout(3500);
    for (let i = 1; i <= 2; i++) {
      await start();
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(3300);
      await census(`${scene}-transition-${i}`);
    }
  }
  await page.goto(`${base}/replays/${fixture.game_id}`, { waitUntil: 'networkidle' });
  await page.locator('[data-beat-index]').waitFor();
  await start();
  await page.waitForTimeout(1000);
  await census('replay-start');
  // Same route, repeated complete public-cut walks: retained heap can be compared at the same beat.
  const last =
    Number(await page.getByRole('slider', { name: 'Seek' }).getAttribute('aria-valuemax')) -
    1;
  for (let cycle = 1; cycle <= 2; cycle++) {
    await start();
    for (let i = 0; i < last; i++) {
      await page.keyboard.press('ArrowRight');
      await page.waitForTimeout(60);
    }
    await page.waitForTimeout(600);
    await census(`replay-end-cycle-${cycle}`);
    for (let i = 0; i < last; i++) await page.keyboard.press('ArrowLeft');
  }
  report.graphics = await page.evaluate(() => {
    const gl = document.createElement('canvas').getContext('webgl');
    const ext = gl?.getExtension('WEBGL_debug_renderer_info');
    return ext ? gl.getParameter(ext.UNMASKED_RENDERER_WEBGL) : 'unavailable';
  });
} finally {
  writeFileSync(output, JSON.stringify(report, null, 2));
  await browser.close();
}
