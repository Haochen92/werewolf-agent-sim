'use client';

/**
 * The replay's departure, held by the route's layout (owner, 2026-10-16): the layout and its
 * `loading.tsx` are what a link prefetches, so the train starts leaving at the click and plays on
 * while the page's code and the log come in. Played by the page (it was, to 2026-10-16), it waited
 * for the page's code: a cold click showed a still saying "Rewinding the reels…", the curtain's
 * last words, and then the platform drawn again from nothing and the whole departure, which read
 * as a crash.
 *
 * The page (TheaterClient) still runs it: it reads when the curtain is down (`useDeparture`) and
 * says what the wait is, when the curtain lifts off its theatre, and when there is nothing to
 * wait for (a dropped game, no such replay), which takes the platform away at once. With
 * `?still=1` (the tests and goldens) there is no departure and the page draws its own still.
 */
import { useParams, useSearchParams } from 'next/navigation';
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { StationDeparture } from '@/stage/scenes/StationDeparture';
import { CURTAIN } from '@/stage/scenes/station';

/** What the page tells the departure. */
export interface DepartureCue {
  /** What the wait is, under the curtain once it is down. */
  line: string;
  /** The theatre is up under the platform: the platform fades off it. */
  lifting: boolean;
  /** Nothing to wait for: the platform goes. */
  off: boolean;
}

interface Departure {
  /** The curtain is down: the page may draw its theatre under it. */
  down: boolean;
  cue: (cue: DepartureCue) => void;
}

const DepartureContext = createContext<Departure | null>(null);

/** The departure over this page, or null where there is none (`?still=1`). */
export function useDeparture(): Departure | null {
  return useContext(DepartureContext);
}

const FIRST: DepartureCue = { line: 'Rewinding the reels…', lifting: false, off: false };

export function DepartureHost({ children }: { children: ReactNode }) {
  const { gameId } = useParams<{ gameId: string }>();
  const still = useSearchParams().get('still') === '1';
  const [down, setDown] = useState(false);
  const onDown = useCallback(() => setDown(true), []);
  const [cue, setCue] = useState(FIRST);
  const [lifted, setLifted] = useState(false);
  useEffect(() => {
    if (!cue.lifting) return;
    const t = setTimeout(() => setLifted(true), CURTAIN.open * 1000);
    return () => clearTimeout(t);
  }, [cue.lifting]);
  const value = useMemo(() => ({ down, cue: setCue }), [down]);

  if (still) return children;
  return (
    <DepartureContext.Provider value={value}>
      <OrientationGuard>
        {children}
        {lifted || cue.off ? null : (
          <StationDeparture
            gameId={gameId}
            line={cue.line}
            onDown={onDown}
            lifting={cue.lifting}
          />
        )}
      </OrientationGuard>
    </DepartureContext.Provider>
  );
}
