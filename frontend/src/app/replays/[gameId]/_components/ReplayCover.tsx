'use client';

/**
 * The replay's way in (owner, 2026-10-16): the house's loading picture (`TrainLoader`) over the
 * page until its theatre is drawn, then faded off it. The train's departure is the live games'
 * only; a replay has nobody boarding and nothing to wait out, so it opens as soon as it can. Held
 * by the route's layout, which a link prefetches with its `loading.tsx`, so the cover is up from
 * the click and is never drawn twice while the page's code and the log come in. Unlike a site
 * page's loader it is there at once and holds at least `MIN_MS`, a replay already in the browser
 * too (2026-10-16: the way into the game is always seen), and the theatre starts only
 * as it lifts (`lifting`), so nothing plays under it.
 *
 * The page (TheaterClient) runs it (`useCover`): what the wait is when it is more than loading
 * (a replay still being filed), when its theatre is drawn and ready, and when there is nothing
 * to wait for (a dropped game, no such replay), which takes it away at once. With `?still=1` (the
 * tests and goldens) there is no cover and the page draws its own loader.
 */
import { useSearchParams } from 'next/navigation';
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { TrainLoader } from '@/components/TrainLoader';
import { OrientationGuard } from '@/stage/OrientationGuard';
import classes from './ReplayCover.module.css';

/** What the page tells the cover. */
export interface CoverCue {
  /** What the wait is, when it is more than loading ("Winding the reels…"). */
  line: string | null;
  /** The theatre is drawn under the cover, its pictures in. */
  ready: boolean;
  /** Nothing to wait for: the cover goes. */
  off: boolean;
}

interface Cover {
  cue: (cue: CoverCue) => void;
  /** The cover is fading off: the theatre is shown and may start. */
  lifting: boolean;
}

const CoverContext = createContext<Cover | null>(null);

/** The cover over this page, or null where there is none (`?still=1`). */
export function useCover(): Cover | null {
  return useContext(CoverContext);
}

const FIRST: CoverCue = { line: null, ready: false, off: false };
/** The least the cover is up, from the click. */
const MIN_MS = 2000;
/** The loader's fade off the theatre (TrainLoader.module.css, `.veil`). */
const LIFT_MS = 400;

export function ReplayCover({ children }: { children: ReactNode }) {
  const still = useSearchParams().get('still') === '1';
  const [cue, setCue] = useState(FIRST);
  const [held, setHeld] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setHeld(true), MIN_MS);
    return () => clearTimeout(t);
  }, []);
  const lifting = cue.ready && held;
  const [lifted, setLifted] = useState(false);
  useEffect(() => {
    if (!lifting) return;
    const t = setTimeout(() => setLifted(true), LIFT_MS);
    return () => clearTimeout(t);
  }, [lifting]);
  const value = useMemo(() => ({ cue: setCue, lifting }), [lifting]);

  if (still) return children;
  return (
    <CoverContext.Provider value={value}>
      <OrientationGuard>
        {children}
        {lifted || cue.off ? null : (
          <div className={classes.cover} data-replay-cover={lifting ? 'lifting' : 'up'}>
            <TrainLoader atOnce leaving={lifting} line={cue.line} />
          </div>
        )}
      </OrientationGuard>
    </CoverContext.Provider>
  );
}
