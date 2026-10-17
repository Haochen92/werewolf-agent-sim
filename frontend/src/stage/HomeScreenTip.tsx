'use client';

/**
 * The one way to the whole screen on an iPhone: Safari there has no fullscreen for a page, but a
 * site added to the Home Screen opens without its bars (manifest.ts). So on an iPhone, in the
 * browser, a line over the stage says how, on the first three visits or until it is dismissed;
 * opened from the Home Screen, or on anything else, it never shows. The phone's own storage
 * remembers; where that is refused (a private window) the line simply shows again. After that
 * the stage's full-screen switch shows it when pressed (`FullScreenButton`, 2026-10-16).
 *
 * Where Chrome will install the house (Android), the switch takes the whole screen itself, and
 * its press also offers the install, for the whole screen every time: the same line with an
 * Install button, until its × ends it for good.
 */
import { useEffect, useState } from 'react';
import { homeScreenOnly, promptInstall } from './fullscreen';
import styles from './HomeScreenTip.module.css';

const KEY = 'ninth-express:home-screen-tip';
/** Shown this many times unasked; the × ends it for good (`DONE`). */
const SHOWS = 3;
const DONE = 99;
/** One page load counts once, however many times the page mounts it. */
let counted = false;
/** How the line says it: Safari's Share menu (an iPhone), or Chrome's install (Android). */
type Way = 'share' | 'install';
/** The lines on the page, for a press that asks for one again (`showHomeScreenTip`). */
const asking = new Set<(way: Way) => void>();

const read = () => {
  try {
    return Number(localStorage.getItem(KEY)) || 0;
  } catch {
    return 0;
  }
};
const write = (n: number) => {
  try {
    localStorage.setItem(KEY, String(n));
  } catch {
    /* no storage: the line shows again next time, which is the lesser harm */
  }
};

/**
 * The line again, from the full-screen switch: on an iPhone whatever its count; Chrome's
 * install only until the line is dismissed for good.
 */
export function showHomeScreenTip(way: Way) {
  if (way === 'install' && read() >= DONE) return;
  asking.forEach((ask) => ask(way));
}

export function HomeScreenTip() {
  const [shown, setShown] = useState<Way | null>(null);
  useEffect(() => {
    const ask = (way: Way) => setShown(way);
    asking.add(ask);
    return () => {
      asking.delete(ask);
    };
  }, []);
  useEffect(() => {
    if (!homeScreenOnly()) return;
    if (!counted) {
      const seen = read();
      if (seen >= SHOWS) return;
      write(seen + 1);
      counted = true;
    } else if (read() >= DONE) return;
    setShown('share');
  }, []);
  if (!shown) return null;
  const dismiss = () => {
    write(DONE);
    setShown(null);
  };
  const installNow = () => {
    promptInstall();
    setShown(null);
  };
  return (
    <div className={styles.tip} role="status">
      <svg viewBox="0 0 24 24" aria-hidden>
        <path d="M12 3v12M8 7l4-4 4 4" />
        <path d="M6 11v8a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-8" />
      </svg>
      {shown === 'share' ? (
        <span>
          For the whole screen, tap Share, then <b>Add to Home Screen</b>, and open the
          house from there.
        </span>
      ) : (
        <>
          <span>For the whole screen every time, install the house.</span>
          <button type="button" className={styles.install} onClick={installNow}>
            Install
          </button>
        </>
      )}
      <button type="button" onClick={dismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
