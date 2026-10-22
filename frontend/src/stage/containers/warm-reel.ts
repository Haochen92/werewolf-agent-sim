/**
 * A preview's reel warmed before it plays (owner, 2026-10-22): the landing's reel jumps from
 * the deal to the night to the vote, and each scene's pictures (the role cards, the night car,
 * its props) were fetched and decoded as the scene arrived, in the middle of its animation (a
 * phone at 4x CPU stalled 100-190 ms at each). The theatre visits the reel's scenes once, still,
 * under its caller's cover, gathers every picture they put on the page, fetches and decodes them,
 * and only then lets the reel play.
 */
import type { SceneBeat } from '@/stage/beats/types';
import type { MotionSpeed } from '@/stage/scenes/types';
import { holdFor } from './transport';

/** The longest the warming may take before the reel plays with whatever has come. */
export const WARM_CAP_MS = 6000;

/**
 * How far into the reel's play the warming reaches: its first scenes, the new ones (the deal,
 * the night, the morning). Warming the whole reel kept the cover up 3 s longer on a phone for
 * scenes a minute away, which the day car's vote had always opened on cold with one stall.
 */
export const WARM_AHEAD_MS = 50_000;

/**
 * The beats to visit within `ahead` ms of the reel's play: the last of each run of neighbouring
 * beats and every beat where the scene changes, the reel's first left out (it is on the page already, and visited last). Within a run
 * a scene's later beats add to its pictures (the deal's faces, the lynch's card), so its last
 * beat stands for it.
 */
export function warmBeats(
  reel: readonly number[],
  beats: readonly SceneBeat[],
  speed: MotionSpeed = 'fast',
  ahead = WARM_AHEAD_MS,
): number[] {
  const out = new Set<number>();
  let at = 0;
  reel.forEach((i, k) => {
    const starts = at;
    at += (beats[i] && holdFor(beats[i], speed)) ?? 0;
    if (k === 0 || starts >= ahead) return;
    const prev = reel[k - 1];
    const next = reel[k + 1];
    const runEnds = next !== i + 1;
    const sceneChanges = beats[i]?.scene !== beats[prev]?.scene || prev !== i - 1;
    if (runEnds || sceneChanges) out.add(i);
  });
  return [...out];
}

const URL_IN_CSS = /url\(["']?([^"')]+)["']?\)/g;

/** Every picture `el` shows now: its `<img>`s, its drawings' `<image>`s and its CSS pictures. */
export function picturesOn(el: Element, into: Set<string>): void {
  el.querySelectorAll('img').forEach((img) => img.currentSrc && into.add(img.currentSrc));
  el.querySelectorAll('image').forEach((img) => {
    const href = img.getAttribute('href');
    if (href) into.add(href);
  });
  for (const node of [el, ...el.querySelectorAll('*')]) {
    const css = getComputedStyle(node);
    for (const value of [css.backgroundImage, css.borderImageSource])
      if (value && value !== 'none')
        for (const m of value.matchAll(URL_IN_CSS))
          if (!m[1].startsWith('data:')) into.add(m[1]);
  }
}

/** The page after a cursor move: the scene committed, measured and its pictures placed. */
export async function settled(el: Element, until: number): Promise<void> {
  while (!el.querySelector('img, image') && Date.now() < until)
    await new Promise((done) => setTimeout(done, 50));
  await new Promise((done) => requestAnimationFrame(() => requestAnimationFrame(done)));
}

/** Fetch and decode every source, or stop at `until`; the images are let go once decoded. */
export async function decodeAll(srcs: Iterable<string>, until: number): Promise<void> {
  const all = [...srcs].map((src) => {
    const img = new Image();
    img.decoding = 'async';
    img.src = src;
    return img.decode().catch(() => {});
  });
  await Promise.race([
    Promise.all(all),
    new Promise((done) => setTimeout(done, Math.max(0, until - Date.now()))),
  ]);
}
