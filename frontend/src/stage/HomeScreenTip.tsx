'use client';

/**
 * The one way to the whole screen on an iPhone: Safari there has no fullscreen for a page, but a
 * site added to the Home Screen opens without its bars (manifest.ts). So on an iPhone, in the
 * browser, a line over the stage says how, on the first three visits or until it is dismissed;
 * opened from the Home Screen, or on anything else, it never shows. The phone's own storage
 * remembers; where that is refused (a private window) the line simply shows again.
 */
import { useEffect, useState } from 'react';
import styles from './HomeScreenTip.module.css';

const KEY = 'ninth-express:home-screen-tip';
/** Shown this many times unasked; the × ends it for good (`DONE`). */
const SHOWS = 3;
const DONE = 99;
/** One page load counts once: the theatre's loading still and then the theatre both mount it. */
let counted = false;

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

export function HomeScreenTip() {
  const [shown, setShown] = useState(false);
  useEffect(() => {
    // an iPhone (an iPad has fullscreen), not already opened from the Home Screen
    const iphone = /iPhone|iPod/.test(navigator.userAgent);
    const standalone =
      window.matchMedia('(display-mode: standalone)').matches ||
      (navigator as Navigator & { standalone?: boolean }).standalone === true;
    if (!iphone || standalone) return;
    if (!counted) {
      const seen = read();
      if (seen >= SHOWS) return;
      write(seen + 1);
      counted = true;
    } else if (read() >= DONE) return;
    setShown(true);
  }, []);
  if (!shown) return null;
  const dismiss = () => {
    write(DONE);
    setShown(false);
  };
  return (
    <div className={styles.tip} role="status">
      <svg viewBox="0 0 24 24" aria-hidden>
        <path d="M12 3v12M8 7l4-4 4 4" />
        <path d="M6 11v8a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-8" />
      </svg>
      <span>
        For the whole screen, tap Share, then <b>Add to Home Screen</b>, and open the house
        from there.
      </span>
      <button type="button" onClick={dismiss} aria-label="Dismiss">
        ×
      </button>
    </div>
  );
}
