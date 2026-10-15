/**
 * The phone's rule as a gate (stage_architecture.md §6, build log §8.3–8.6): on a phone nothing
 * animates at rest inside the stage, nothing keeps `will-change` but the world, no large mask,
 * and no large painted area moves or fades while a beat arrives (a camera move, a full-stage
 * crossfade). Each of those is a GPU layer on iPhone Safari, plus every stage layer drawn over
 * it, and the page dies at its memory line; four rounds of crashes were each one more instance
 * of the same rule, so the rule is walked here over every scene and every beat in the phone
 * frame (`frame=iphone14`, so `data-small` applies), with the X-ray on where it changes the
 * stage. A finding is a failure; scrollers are listed for information only (iPhone Safari gives
 * each its own layer too, which this cannot weigh).
 */
import { test, expect, type Page } from '@playwright/test';

/** Each scene the workbench knows, and whether the X-ray changes what it draws. */
const SCENES: [scene: string, xray: boolean, spectator: boolean][] = [
  ['station', false, true],
  ['deal', false, true],
  ['day', true, true],
  ['vote', true, true],
  ['lynch', true, true],
  ['night', false, true], // the X-ray's night is `rnight`; with the X-ray on this scene has no beats
  ['room', false, true],
  ['pack', false, true],
  ['morning', true, true],
  ['rnight', true, false], // the replay's night exists only with the X-ray on
  ['over', false, true],
];

/** How long a beat's arrival is watched (the longest arrival is about 3 s). */
const WATCH_MS = 3200;
/** A painted area at or above this share of the stage counts as large (a figure or a prop crossing
 * the stage on a phone is under two-thirds; the camera, a crossfade or a panel is more). */
const LARGE = 0.6;
const MASK_LARGE = 0.05;
/** Style writes within the window at or above this count mean a move, not a cut. */
const MOVES = 6;

interface Finding {
  beat: string;
  kind: 'idle-animation' | 'will-change' | 'mask' | 'mover' | 'remount';
  what: string;
}

/**
 * A beat must not rebuild its scene's set (the wing, the house light, a night room's
 * picture): rebuilt per beat, the set is a burst of script and paint at the beat's start, and
 * the pictures decode again (build log §8.8–8.9). These scenes are still keyed whole per beat
 * and short; their remounts are listed, not failed, until they are split.
 */
const KEYED_WHOLE = new Set(['deal', 'over', 'station']);

/**
 * What a beat keeps: the wing itself, the house light's sheet (not the specials' cones, which
 * come and go with the beat), a night room's picture. The wing's tiles may change kind under
 * it (with Reveal on, a tile with a read is a button and one without is not), so remounted
 * heads are listed, not failed.
 */
const SET_MARKS = [
  '[data-layer=hud] [data-cols]',
  '[data-layer=light] [data-house-light] .stage-paint',
  '[data-layer=paint] [data-room] img',
];
const TILE_MARK = '[data-layer=hud] [data-cols] img';

declare global {
  interface Window {
    __rule: {
      start(): void;
      stop(): {
        findings: Omit<Finding, 'beat'>[];
        info: string[];
        remounted: string[];
        room: string;
      };
    };
  }
}

/* installed before the page's scripts: watches style writes inside the stage, then reads the
   rule's four checks; everything here runs in the page */
const INSTALL = `(() => {
  const LARGE = ${LARGE}, MASK_LARGE = ${MASK_LARGE}, MOVES = ${MOVES};
  const SET_MARKS = ${JSON.stringify([...SET_MARKS, TILE_MARK])};
  let counts = new Map(), mo = null, marks = [];
  const roomOf = () => { const r = document.querySelector('[data-layer=paint] [data-room]'); return r ? r.getAttribute('data-room') : ''; };
  const box = () => document.querySelector('[data-small]');
  const name = (el) => {
    const one = (e) => {
      const c = (e.getAttribute && e.getAttribute('class')) || '';
      const data = e.getAttributeNames ? e.getAttributeNames().filter((a) => a.startsWith('data-') && a !== 'data-small').map((a) => a + (e.getAttribute(a) ? '=' + e.getAttribute(a) : '')).slice(0, 2).join(' ') : '';
      return e.tagName.toLowerCase() + (c ? '.' + String(c).split(' ').slice(0, 2).join('.') : '') + (data ? '[' + data + ']' : '');
    };
    // an unnamed div is told by its nearest named ancestor and the layer it sits in
    let s = one(el), up = el.parentElement, hops = 0;
    while (up && hops < 4 && !/\\.|\\[/.test(s)) { s = one(el) + ' in ' + one(up); if (/\\.|\\[/.test(one(up))) break; up = up.parentElement; hops++; }
    const layer = el.closest && el.closest('[data-layer]');
    return s + (layer ? ' (layer ' + layer.getAttribute('data-layer') + ')' : '');
  };
  // the share of the stage an element paints: the union of its leaves' boxes (pictures, svg,
  // backgrounds, text), not its own box, since many movers are full-stage wrappers round one figure
  const painted = (el) => {
    const b = box(); if (!b) return 0;
    const B = b.getBoundingClientRect(); const A = B.width * B.height; if (!A) return 0;
    let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9, any = false;
    const take = (r) => { if (r.width < 1 || r.height < 1) return; any = true; x0 = Math.min(x0, r.left); y0 = Math.min(y0, r.top); x1 = Math.max(x1, r.right); y1 = Math.max(y1, r.bottom); };
    // a picture is its box; an svg is what it draws (its box is often the whole stage)
    for (const l of el.querySelectorAll('img, canvas, video')) take(l.getBoundingClientRect());
    for (const l of el.querySelectorAll('svg')) { let k = 0; for (const d of l.querySelectorAll('image, path, rect, circle, ellipse, polygon, polyline, line, text, use, foreignObject')) { if (k++ > 600) break; take(d.getBoundingClientRect()); } }
    let seen = 0;
    const walker = document.createTreeWalker(el, NodeFilter.SHOW_ELEMENT | NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n && seen < 4000; n = walker.nextNode(), seen++) {
      if (n.nodeType === 3) { if (n.textContent.trim()) { const r = document.createRange(); r.selectNodeContents(n); take(r.getBoundingClientRect()); } continue; }
      if (n.closest('svg')) continue;
      const cs = getComputedStyle(n);
      if (cs.backgroundImage !== 'none' || (cs.backgroundColor !== 'rgba(0, 0, 0, 0)' && cs.backgroundColor !== 'transparent') || cs.boxShadow !== 'none' || cs.borderStyle !== 'none') take(n.getBoundingClientRect());
    }
    if (el.matches && el.matches('img, canvas, video')) take(el.getBoundingClientRect());
    if (!any) return 0;
    const ix0 = Math.max(x0, B.left), iy0 = Math.max(y0, B.top), ix1 = Math.min(x1, B.right), iy1 = Math.min(y1, B.bottom);
    return Math.max(0, ix1 - ix0) * Math.max(0, iy1 - iy0) / A;
  };
  const pct = (f) => Math.round(f * 100) + '%';
  let samples = null, seenAnim = new Map();
  const sample = () => {
    const b = box(); if (!b) return;
    for (const a of document.getAnimations()) {
      const el = a.effect && a.effect.target; if (!el || !b.contains(el) || a.playState !== 'running') continue;
      const t = a.effect.getTiming ? a.effect.getTiming() : {};
      const s = seenAnim.get(el) || { n: 0, name: a.animationName || (a.effect.getKeyframes ? Object.keys(a.effect.getKeyframes()[0] || {}).filter((p) => !/^(offset|easing|composite|computedOffset)$/.test(p)).join('/') : 'animation'), ms: t.duration };
      s.n++; seenAnim.set(el, s);
    }
  };
  const start = () => {
    stopObserving(); counts = new Map(); seenAnim = new Map();
    if (samples) clearInterval(samples); samples = setInterval(sample, 150);
    // the set's elements before the step: still in the document after it, or remounted
    marks = SET_MARKS.map((sel) => [sel, [...document.querySelectorAll(sel)]]);
    const b = box(); if (!b) return;
    mo = new MutationObserver((recs) => { for (const r of recs) counts.set(r.target, (counts.get(r.target) || 0) + 1); });
    mo.observe(b, { attributes: true, attributeFilter: ['style', 'transform', 'opacity'], subtree: true });
  };
  const stopObserving = () => { if (mo) { mo.disconnect(); mo = null; } if (samples) { clearInterval(samples); samples = null; } };
  const stop = () => {
    stopObserving();
    const findings = [], info = [];
    const remounted = marks.map(([sel, els]) => [sel, els.filter((el) => !el.isConnected).length, els.length]).filter(([, gone]) => gone > 0).map(([sel, gone, n]) => sel + ' (' + gone + ' of ' + n + ')');
    const room = roomOf();
    const b = box();
    if (!b) return { findings: [{ kind: 'mover', what: 'no [data-small] stage on the page: the phone frame is not applied' }], info, remounted, room };
    for (const [el, n] of counts) {
      if (n < MOVES || !el.isConnected) continue;
      const share = painted(el);
      if (share >= LARGE) findings.push({ kind: 'mover', what: name(el) + ' paints ' + pct(share) + ' of the stage, ' + n + ' style writes in ' + ${WATCH_MS} + ' ms' + (getComputedStyle(el).filter !== 'none' ? ', with a filter' : '') });
    }
    // a large element seen animating in two samples or more (300 ms+) is a GPU layer for that
    // long, and every layer drawn over it: the window's own moves are caught here, not only
    // what is still running at its end
    for (const [el, s] of seenAnim) {
      if (s.n < 2 || !el.isConnected) continue;
      const share = painted(el);
      if (share >= LARGE) findings.push({ kind: 'mover', what: name(el) + ': ' + s.name + ' ' + (s.ms || '?') + ' ms seen in ' + s.n + ' samples, paints ' + pct(share) });
    }
    for (const a of document.getAnimations()) {
      const t = a.effect && a.effect.getTiming ? a.effect.getTiming() : {};
      const el = a.effect && a.effect.target;
      if (!el || !b.contains(el)) continue;
      const long = t.iterations === Infinity || (typeof t.duration === 'number' && t.duration > 8000);
      const share = painted(el);
      if (long) findings.push({ kind: 'idle-animation', what: name(el) + ': ' + (a.animationName || 'animation') + ' ' + (t.iterations === Infinity ? 'infinite' : t.duration + ' ms') + ', paints ' + pct(share) });
      else if (share >= LARGE && a.playState === 'running') findings.push({ kind: 'mover', what: name(el) + ': ' + (a.animationName || 'animation') + ' ' + t.duration + ' ms still running after the window, paints ' + pct(share) });
    }
    const all = b.querySelectorAll('*');
    for (const el of all) {
      if (el.closest('svg') && el.tagName.toLowerCase() !== 'svg') continue;
      const cs = getComputedStyle(el);
      if (cs.willChange !== 'auto' && !/Stage_world/.test(el.className || '')) findings.push({ kind: 'will-change', what: name(el) + ': will-change ' + cs.willChange });
      const mask = cs.maskImage !== 'none' ? cs.maskImage : (cs.webkitMaskImage && cs.webkitMaskImage !== 'none' ? cs.webkitMaskImage : null);
      if (mask) { const r = el.getBoundingClientRect(), B = b.getBoundingClientRect(); const share = (r.width * r.height) / (B.width * B.height); if (share >= MASK_LARGE) findings.push({ kind: 'mask', what: name(el) + ' masked over ' + pct(share) }); }
      if ((cs.overflowY === 'auto' || cs.overflowY === 'scroll') && el.scrollHeight > el.clientHeight + 2) info.push(name(el) + ' scrolls ' + Math.round(el.clientWidth) + 'x' + Math.round(el.clientHeight) + ' css px over ' + Math.round(el.scrollHeight) + ' px of content');
    }
    return { findings, info, remounted, room };
  };
  window.__rule = { start, stop };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start); else start();
})();`;

async function walk(page: Page, scene: string, viewer: 'spectator' | 'xray') {
  await page.addInitScript(INSTALL);
  const q = viewer === 'xray' ? '&viewer=xray' : '';
  await page.goto(`/workbench/${scene}?beat=0&animate=1&frame=iphone14${q}`, {
    waitUntil: 'load',
  });
  const n = Number((await page.locator('body').innerText()).match(/of (\d+)/)?.[1] ?? 0);
  const findings: Finding[] = [];
  const scrollers = new Set<string>();
  let prev: { beat: string; room: string } | null = null;
  for (let i = 0; i < n; i++) {
    if (i > 0) {
      await page.evaluate(() => window.__rule.start());
      await page.keyboard.press('ArrowRight');
    }
    await page.waitForTimeout(WATCH_MS);
    const beat =
      (await page.locator('body').innerText()).match(/([a-z]+\.[a-z0-9-]+) · seq/)?.[1] ??
      `#${i}`;
    const r = await page.evaluate(() => window.__rule.stop());
    for (const f of r.findings) findings.push({ beat: `${scene}#${i} ${beat}`, ...f });
    for (const s of r.info) scrollers.add(s);
    // the set is kept within a scene: a new room (the replay's night, one actor at a time) or
    // the night's hub giving way to a room is a new set
    const sameSet =
      !!prev &&
      prev.room === r.room &&
      !(beat.startsWith('rnight.') && prev.beat !== beat && beat !== 'rnight.spoke');
    if (sameSet && r.remounted.length) {
      const what = `the set is rebuilt by this beat: ${r.remounted.join(', ')}`;
      const tilesOnly = r.remounted.every((m) => m.startsWith(TILE_MARK));
      if (KEYED_WHOLE.has(scene) || tilesOnly)
        scrollers.add(`${scene}#${i} ${beat}: ${what}`);
      else findings.push({ beat: `${scene}#${i} ${beat}`, kind: 'remount', what });
    }
    prev = { beat, room: r.room };
  }
  return { n, findings, scrollers: [...scrollers] };
}

for (const [scene, xray, spectator] of SCENES) {
  const viewers: ('spectator' | 'xray')[] = [];
  if (spectator) viewers.push('spectator');
  if (xray) viewers.push('xray');
  for (const viewer of viewers) {
    test(`phone rule: ${scene}, ${viewer}`, async ({ page }, testInfo) => {
      testInfo.setTimeout(15 * 60_000);
      const { n, findings, scrollers } = await walk(page, scene, viewer);
      expect(n, 'the scene has beats').toBeGreaterThan(0);
      const report =
        `${scene} (${viewer}): ${n} beats, ${findings.length} findings\n` +
        findings.map((f) => `  ${f.beat}  [${f.kind}]  ${f.what}`).join('\n') +
        (scrollers.length
          ? `\n  scrollers (information):\n` + scrollers.map((s) => `    ${s}`).join('\n')
          : '');
      await testInfo.attach('phone-rule', { body: report, contentType: 'text/plain' });
      console.log(report);
      expect(findings, report).toEqual([]);
    });
  }
}
