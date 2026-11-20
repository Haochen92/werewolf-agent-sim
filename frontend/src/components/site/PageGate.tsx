'use client';
/**
 * A site page comes up whole (owner, 2026-10-18): until the pictures on its first screen and its
 * fonts are in, the page under the nav is hidden behind the house's loading picture, then it
 * fades in at once. Shown as it arrived, a first visit with nothing cached put the words on bare
 * black and painted each wall in from the top, seconds later.
 *
 * Put it first in the page's `<main>`. It reads the pictures off the page itself (the `<img>`s
 * and the stylesheet's backgrounds on the screen), so a page lists nothing. The loader comes up
 * only after 1 s and then stays 2 s, so a cached visit never sees it; 8 s ends the wait whatever
 * is missing.
 *
 * The wait (`gate`) runs as the page arrives, from an inline script, not once React is up: a
 * cached visit opens as soon as the page is parsed, before the page's code has started. A page
 * reached by a click runs the same wait from React. A reader without script (a crawler) gets the
 * page as it is. `usePageOpen` tells a later section of the page that the first screen is up, so
 * it can start loading its own (the landing carriage).
 */
import {
  useEffect,
  useLayoutEffect,
  useRef,
  useState,
  useSyncExternalStore,
  type CSSProperties,
} from 'react';
import { TrainLoader } from '@/components/TrainLoader';
import classes from './PageGate.module.css';

/** How long the page waits on its pictures before it comes up without them. */
const CAP_MS = 8000;
/** The fade off the loader and onto the page (PageGate.module.css). */
const LIFT_MS = 400;
/** When the loader comes up, unless it follows one already up (PageGate.module.css): under a
 *  second a wait needs no sign, and a train shown sooner mostly blinks (owner, 2026-10-18). */
const SHOW_MS = 1000;
/** Once up, how long the loader stays at least, so it is seen, never a blink (owner,
 *  2026-10-18). */
const HOLD_MS = 2000;

type GateRun = { root: Element | null; ready: Promise<void> | null };
type GateWindow = { __gateRun?: GateRun | null };

/**
 * Hides the page under `root`, waits until the pictures on the screen and the fonts are loaded and
 * decoded (or `cap` ms), then shows it, fading in for `lift` ms. A loader that came up (`show` ms
 * in) stays `hold` ms before it goes; a wait over before `show` shows nothing. Plain script that uses nothing
 * from outside itself: it is also written into the page as text (`INLINE`), so it can run as the
 * page arrives. A later run (another page) makes an earlier one's ending do nothing.
 */
function gate(
  root: Element | null,
  cap: number,
  lift: number,
  show: number,
  hold: number,
): Promise<void> {
  const t0 = performance.now();
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
  run.ready = Promise.race([pictures, new Promise((done) => setTimeout(done, cap))])
    .then(() => {
      const up = performance.now() - t0;
      const shown = up > show;
      const rest = shown ? show + hold - up : 0;
      return new Promise<boolean>((done) =>
        setTimeout(() => done(shown), rest > 0 ? rest : 0),
      );
    })
    .then((shown) => {
      if (w.__gateRun !== run) return;
      html.removeAttribute('data-gate');
      // a page ready before the loader came up is simply there: no fade (PageGate.module.css)
      html.setAttribute('data-gate-lift', shown ? '' : 'quick');
      setTimeout(() => {
        if (w.__gateRun === run) html.removeAttribute('data-gate-lift');
      }, lift);
    });
  return run.ready;
}

/** The page's inline script: the wait, from where the script stands in the page's `<main>`. */
const INLINE = `(${gate.toString()})(document.currentScript&&document.currentScript.closest('main'),${CAP_MS},${LIFT_MS},${SHOW_MS},${HOLD_MS})`;

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

// What the loaders share lives on the window, not in this module: the build puts a copy of this
// module in the site loader's bundle and another in the pages', each with its own variables, and a
// page's gate never saw the loader's train (it blinked, went dark, and came back).
type GateNav = {
  /** The site loader (`(site)/loading.tsx`) came on the page, and went (null while it is up). */
  routeFrom?: number;
  routeTo?: number | null;
  /** When the visitor last asked for a page: a click on one of the site's links, back or forward. */
  askedAt?: number;
};
const nav = (): GateNav => {
  const w = window as unknown as { __gateNav?: GateNav };
  return (w.__gateNav ??= {});
};

// the site's own loader while a page's code comes: a gate that follows a train already up carries
// it on, at once and with what it has shown counted to its hold (owner, 2026-10-18)
/** Put in `(site)/loading.tsx`: marks while its loader is on the page. */
export function RouteWaitMark() {
  useEffect(() => {
    nav().routeFrom = performance.now();
    nav().routeTo = null;
    return () => {
      nav().routeTo = performance.now();
    };
  }, []);
  return null;
}
/** How long the site loader's train has been up, in ms; 0 when it is not. Read as the page
 *  renders, so the loader is usually still on the page (it goes when the page commits). */
function trainUpFor(): number {
  const { routeFrom, routeTo } = nav();
  if (routeFrom === undefined) return 0;
  const now = performance.now();
  if (routeTo != null && now - routeTo > 200) return 0;
  return Math.max(0, (routeTo ?? now) - routeFrom - SHOW_MS);
}

// a page reached by a click counts its loader's second from the click, not from when its code
// arrived, or a slow click sat dark for that wait and a second more (owner, 2026-10-18)
if (
  typeof window !== 'undefined' &&
  !(window as unknown as { __gateAsk?: true }).__gateAsk
) {
  (window as unknown as { __gateAsk?: true }).__gateAsk = true;
  document.addEventListener(
    'click',
    (e) => {
      const a = e.target instanceof Element ? e.target.closest('a[href]') : null;
      if (a instanceof HTMLAnchorElement && a.origin === location.origin)
        nav().askedAt = performance.now();
    },
    true,
  );
  window.addEventListener('popstate', () => {
    nav().askedAt = performance.now();
  });
}

/** How this page's train starts: carried on from the site loader's, up `carried` ms already, or
 *  due `show` ms from now (from the click that asked for the page, when there was one). */
function trainStart(): { carried: number; show: number } {
  const carried = trainUpFor();
  if (carried > 0) return { carried, show: -carried };
  const since = performance.now() - (nav().askedAt ?? -Infinity);
  return { carried: 0, show: since < CAP_MS ? Math.max(0, SHOW_MS - since) : SHOW_MS };
}

const useLayoutEffectOnClient = typeof window === 'undefined' ? useEffect : useLayoutEffect;

export function PageGate() {
  const ref = useRef<HTMLDivElement>(null);
  const [phase, setPhase] = useState<'wait' | 'done'>('wait');
  const [start] = useState(() =>
    typeof window !== 'undefined' ? trainStart() : { carried: 0, show: SHOW_MS },
  );

  useLayoutEffectOnClient(() => {
    const root = ref.current?.parentElement ?? null;
    const w = window as unknown as GateWindow;
    // the page's inline script has been waiting since the page arrived; a page reached by a
    // click (React does not run a script it puts on the page) starts its own wait here
    const run = w.__gateRun;
    const ready =
      run && run.root === root && run.ready
        ? run.ready
        : gate(root, CAP_MS, LIFT_MS, start.show, HOLD_MS);
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
    <div
      ref={ref}
      className={classes.cover}
      style={{ '--show': `${Math.max(0, start.show)}ms` } as CSSProperties}
      data-gate-cover=""
    >
      <script dangerouslySetInnerHTML={{ __html: INLINE }} />
      <TrainLoader atOnce={start.carried > 0} />
    </div>
  );
}
