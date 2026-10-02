'use client';

/**
 * The stage only plays in landscape (stage_architecture.md §3, ruling 3). On a phone that can
 * be told to turn (Android's Chrome), the first tap asks for fullscreen and locks the screen
 * sideways. Where a page is not allowed to do that (Safari on the iPhone), a card over the page
 * asks the viewer to turn the phone, for as long as it is held upright. There is no portrait
 * layout behind it.
 *
 * The card is pure CSS on the viewport's orientation, so it is right from the first paint.
 * The fullscreen request only happens on a touch screen: on a computer it would be a surprise.
 * An iPhone in Safari also gets the home-screen tip (`HomeScreenTip`), the one way to the whole
 * screen there.
 */
import { useEffect, useRef, type ReactNode } from 'react';
import { HomeScreenTip } from './HomeScreenTip';
import styles from './OrientationGuard.module.css';

/** `screen.orientation.lock` is not in every TypeScript DOM lib yet. */
type Lockable = ScreenOrientation & { lock?: (o: 'landscape') => Promise<void> };

export function OrientationGuard({ children }: { children: ReactNode }) {
  const asked = useRef(false);
  useEffect(() => {
    if (!window.matchMedia('(pointer: coarse)').matches) return;
    const root = document.documentElement;
    const orientation = screen.orientation as Lockable | undefined;
    if (!root.requestFullscreen || !orientation?.lock) return;
    // both need a user gesture, so they wait for the first touch
    const onFirst = () => {
      if (asked.current) return;
      asked.current = true;
      root
        .requestFullscreen({ navigationUI: 'hide' })
        .then(() => orientation.lock?.('landscape'))
        .catch(() => {});
    };
    window.addEventListener('pointerup', onFirst, { once: true });
    return () => window.removeEventListener('pointerup', onFirst);
  }, []);

  return (
    <>
      {children}
      <HomeScreenTip />
      <div className={styles.turn} role="alert">
        <svg viewBox="0 0 64 64" aria-hidden>
          <rect x="22" y="8" width="20" height="36" rx="4" />
          <path d="M14 50a22 22 0 0 0 36 0" />
          <path d="M50 50l-6 -1M50 50l1 -6" />
        </svg>
        <strong>Turn your phone</strong>
        <span>
          The stage plays sideways. On a computer, make the window wider than it is tall.
        </span>
      </div>
    </>
  );
}
