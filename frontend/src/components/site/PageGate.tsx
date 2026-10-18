'use client';
/**
 * A site page comes up whole (owner, 2026-10-18): until the pictures on its first screen and its
 * fonts are in, the page under the nav is hidden behind the house's loading picture, then it
 * fades in at once. Shown as it arrived, a first visit with nothing cached put the words on bare
 * black and painted each wall in from the top, seconds later.
 *
 * Put it first in the page's `<main>`. It reads the pictures off the page itself (the `<img>`s
 * and the stylesheet's backgrounds on the screen), so a page lists nothing. The loader comes up
 * only after 0.3 s, so a cached visit never sees it; 8 s ends the wait whatever is missing.
 *
 * The wait (`gate`) runs as the page arrives, from an inline script, not once React is up: a
 * cached visit opens as soon as the page is parsed, before the page's code has started. A page
 * reached by a click runs the same wait from React. A reader without script (a crawler) gets the
 * page as it is. `usePageOpen` tells a later section of the page that the first screen is up, so
 * it can start loading its own (the landing carriage).
 */
import { useEffect, useLayoutEffect, useRef, useState, useSyncExternalStore } from 'react';
import { TrainLoader } from '@/components/TrainLoader';
import classes from './PageGate.module.css';

/** How long the page waits on its pictures before it comes up without them. */
const CAP_MS = 8000;
/** The fade off the loader and onto the page (PageGate.module.css). */
const LIFT_MS = 400;

type GateRun = { root: Element | null; ready: Promise<void> | null };
type GateWindow = { __gateRun?: GateRun | null };

/**
 * Hides the page under `root`, waits until the pictures on the screen and the fonts are loaded and
 * decoded (or `cap` ms), then shows it, fading in for `lift` ms. Plain script that uses nothing
 * from outside itself: it is also written into the page as text (`INLINE`), so it can run as the
 * page arrives. A later run (another page) makes an earlier one's ending do nothing.
 */
function gate(root: Element | null, cap: number, lift: number): Promise<void> {
  const html = document.documentElement;
  const w = window as unknown as GateWindow;
  const run: GateRun = { root: root, ready: null };
  w.__gateRun = run;
  html.setAttribute('data-gate', '');
  html.removeAttribute('data-gate-lift');
  const frame = () => new Promise((done) => requestAnimationFrame(done));
  const parsed =
    document.readyState === 'loading'
      ? new Promise((done) =>
          document.addEventListener('DOMContentLoaded', done, { once: true }),
        )
      : Promise.resolve();
  // the page places its pictures over its first renders: two frames, and they are on it
  const pictures = parsed
    .then(frame)
    .then(frame)
    .then(() => {
      const h = window.innerHeight;
      const waits: Promise<unknown>[] = [document.fonts.ready];
      const urls: Record<string, true> = {};
      const look = (el: Element) => {
        const r = el.getBoundingClientRect();
        if (!(r.width > 0 && r.height > 0 && r.bottom > 0 && r.top < h)) return;
        if (el.tagName === 'IMG')
          waits.push((el as HTMLImageElement).decode().catch(() => {}));
        [null, '::before', '::after'].forEach((pseudo) => {
          const bg = getComputedStyle(el, pseudo).backgroundImage;
          const re = /url\("?([^")]+)"?\)/g;
          let m;
          while (bg !== 'none' && (m = re.exec(bg))) urls[m[1]] = true;
        });
      };
      if (root) {
        look(root);
        root.querySelectorAll('*').forEach(look);
      }
      Object.keys(urls).forEach((src) => {
        const img = new Image();
        img.src = src;
        waits.push(img.decode().catch(() => {}));
      });
      return Promise.all(waits);
    });
  run.ready = Promise.race([pictures, new Promise((done) => setTimeout(done, cap))]).then(
    () => {
      if (w.__gateRun !== run) return;
      html.removeAttribute('data-gate');
      html.setAttribute('data-gate-lift', '');
      setTimeout(() => {
        if (w.__gateRun === run) html.removeAttribute('data-gate-lift');
      }, lift);
    },
  );
  return run.ready;
}

/** The page's inline script: the wait, from where the script stands in the page's `<main>`. */
const INLINE = `(${gate.toString()})(document.currentScript&&document.currentScript.closest('main'),${CAP_MS},${LIFT_MS})`;

// whether the page's first screen is up, for the sections below it
let open = false;
const listeners = new Set<() => void>();
function setOpen(next: boolean) {
  open = next;
  listeners.forEach((l) => l());
}
function subscribe(l: () => void) {
  listeners.add(l);
  return () => {
    listeners.delete(l);
  };
}

/** True once the page's first screen is up. */
export function usePageOpen(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => open,
    () => false,
  );
}

// the site's own loader (`(site)/loading.tsx`) while a page's code comes: a gate that follows a
// loader already up shows its own at once, or the train would go and come back
let routeWait: { from: number; to: number | null } | null = null;
/** Put in `(site)/loading.tsx`: marks while its loader is on the page. */
export function RouteWaitMark() {
  useEffect(() => {
    routeWait = { from: performance.now(), to: null };
    return () => {
      if (routeWait) routeWait.to = performance.now();
    };
  }, []);
  return null;
}
function followsLoader(): boolean {
  if (!routeWait?.to) return false;
  return routeWait.to - routeWait.from > 300 && performance.now() - routeWait.to < 200;
}

const useLayoutEffectOnClient = typeof window === 'undefined' ? useEffect : useLayoutEffect;

export function PageGate() {
  const ref = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<'wait' | 'done'>('wait');
  const [atOnce] = useState(() => typeof window !== 'undefined' && followsLoader());

  useLayoutEffectOnClient(() => {
    const root = ref.current?.parentElement ?? null;
    const w = window as unknown as GateWindow;
    // the page's inline script has been waiting since the page arrived; a page reached by a
    // click (React does not run a script it puts on the page) starts its own wait here
    const run = w.__gateRun;
    const ready =
      run && run.root === root && run.ready ? run.ready : gate(root, CAP_MS, LIFT_MS);
    setOpen(false);
    let live = true;
    let t: ReturnType<typeof setTimeout> | undefined;
    void ready.then(() => {
      if (!live) return;
      setOpen(true);
      t = setTimeout(() => setPhase('done'), LIFT_MS);
    });
    return () => {
      live = false;
      clearTimeout(t);
      if (w.__gateRun?.root === root) {
        w.__gateRun = null;
        document.documentElement.removeAttribute('data-gate');
        document.documentElement.removeAttribute('data-gate-lift');
      }
    };
  }, []);

  if (phase === 'done') return null;
  return (
    <div ref={ref} className={classes.cover} data-gate-cover="">
      <script dangerouslySetInnerHTML={{ __html: INLINE }} />
      <TrainLoader atOnce={atOnce} />
    </div>
  );
}
