'use client';

/**
 * The stage's full-screen switch (owner, 2026-10-16), beside the music's: a press takes the
 * whole screen where the page may (and turns a phone's stage sideways), and a second gives it
 * back. On an iPhone in Safari, which has no fullscreen for a page, it shows the line that says
 * how (`HomeScreenTip`), so the way is there after the line's own three showings are spent;
 * opened from the Home Screen, already the whole screen, it is not drawn. Where Chrome will
 * install the house on a phone, the press also offers that (the same line, with an Install
 * button).
 */
import { useEffect, useState } from 'react';
import { canFullscreen, canInstall, enterFullscreen, homeScreenOnly } from './fullscreen';
import { showHomeScreenTip } from './HomeScreenTip';

export function FullScreenButton({ className }: { className?: string }) {
  const [mode, setMode] = useState<'screen' | 'tip' | null>(null);
  const [full, setFull] = useState(false);
  useEffect(() => {
    setMode(homeScreenOnly() ? 'tip' : canFullscreen() ? 'screen' : null);
    const change = () => setFull(!!document.fullscreenElement);
    change();
    document.addEventListener('fullscreenchange', change);
    return () => document.removeEventListener('fullscreenchange', change);
  }, []);
  if (!mode) return null;
  const label = full ? 'Leave full screen' : 'Full screen';
  const press = () => {
    if (mode === 'tip') return showHomeScreenTip('share');
    if (full) return void document.exitFullscreen().catch(() => {});
    void enterFullscreen();
    // a phone's (Android's): on a computer the house is a tab like any other
    if (canInstall() && window.matchMedia('(pointer: coarse)').matches)
      showHomeScreenTip('install');
  };
  return (
    <button
      type="button"
      className={className}
      aria-label={label}
      title={label}
      onClick={press}
    >
      <svg viewBox="0 0 24 24" aria-hidden="true">
        <path
          d={
            full
              ? 'M9 4v5H4M15 4v5h5M9 20v-5H4M15 20v-5h5'
              : 'M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5'
          }
          fill="none"
          stroke="currentColor"
          strokeWidth={1.8}
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </button>
  );
}
