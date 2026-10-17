'use client';

/**
 * The way into a live game (owner, 2026-10-17): the house's loading picture (`TrainLoader`)
 * from the click, or a reload's first paint, until the page has something to show, then faded
 * off it. Every wait on this route is this one picture: the route's `loading.tsx`, the page's
 * Suspense fallback and its wait for the status or a rejoin draw nothing of their own, so the
 * loader is drawn once and never swapped for another (before, the still platform,
 * `StationStill`, stood there and was torn down for the departure, which read as a crash). Held
 * by the route's layout, as the replay's cover is (`ReplayCover`), so it is up from the click.
 *
 * The page tells it what it waits for (`useGameCover`): the status (no ceiling: it either
 * comes or fails), the platform's pictures (a game for one's, or a room's: lifted once its train
 * and country are in, or after `MAX_UP_MS`), nothing more (`ready`: faded off), or nothing at
 * all (`off`: gone at once, so what went wrong is said).
 */
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from 'react';
import { TrainLoader } from '@/components/TrainLoader';
import classes from './GameCover.module.css';

export type CoverWait = 'status' | 'platform' | 'ready' | 'off';

export interface CoverCue {
  wait: CoverWait;
  /** What the wait is, when it is more than loading ("Reclaiming your seat…"). */
  line?: string | null;
}

const CoverContext = createContext<((cue: CoverCue) => void) | null>(null);

/** Tell the cover over this page what it waits for; null outside the route. */
export function useGameCover(): ((cue: CoverCue) => void) | null {
  return useContext(CoverContext);
}

/** The loader's fade off the page (TrainLoader.module.css, `.veil`). */
const LIFT_MS = 400;
/** However the platform goes, the cover never outstays this: a stuck loader reads as a dead page. */
const MAX_UP_MS = 12_000;

export function GameCover({ children }: { children: ReactNode }) {
  const [cue, setCue] = useState<CoverCue>({ wait: 'status' });
  const [lifted, setLifted] = useState(false);
  const tell = useCallback((next: CoverCue) => {
    setCue(next);
    // a wait that starts again (a seat to reclaim mid-game) brings the picture back
    if (next.wait === 'status') setLifted(false);
  }, []);
  const [ceiling, setCeiling] = useState(false);
  useEffect(() => {
    const t = setTimeout(() => setCeiling(true), MAX_UP_MS);
    return () => clearTimeout(t);
  }, []);
  const lifting = cue.wait === 'ready' || (cue.wait === 'platform' && ceiling);
  useEffect(() => {
    if (!lifting) return;
    const t = setTimeout(() => setLifted(true), LIFT_MS);
    return () => clearTimeout(t);
  }, [lifting]);
  const up = !lifted && cue.wait !== 'off';

  return (
    <CoverContext.Provider value={tell}>
      {children}
      {up ? (
        <div className={classes.cover} data-game-cover={lifting ? 'lifting' : 'up'}>
          <TrainLoader atOnce leaving={lifting} line={cue.line ?? null} />
        </div>
      ) : null}
    </CoverContext.Provider>
  );
}
