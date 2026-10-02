'use client';

/**
 * What the stage knows about the screen it is on: only whether it is a phone's. A phone's
 * browser gives one page a fixed memory budget and kills the page at the line, so the heaviest
 * moments (two backdrop sheets crossfading, a full-stage fade) take a cheaper form there (build
 * log §8.3). The server renders for a desktop; the browser corrects itself once mounted.
 */
import { useEffect, useState } from 'react';

/** Narrower than this, in css px, and the window is a phone's (landscape). */
export const NARROW_PX = 1000;

export function useNarrow(): boolean {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    setNarrow(window.innerWidth < NARROW_PX);
  }, []);
  return narrow;
}
