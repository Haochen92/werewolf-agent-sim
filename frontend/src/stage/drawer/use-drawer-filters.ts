'use client';

/**
 * The drawer's filters as state, for whoever mounts the stage (the workbench, the replay, the
 * live game). They live above the scenes because a scene is redrawn at every beat, and a
 * viewer who picked "Day 3" or one seat expects that to hold while the game plays on.
 *
 * `scroll` is the same idea for the reading place: a new scene mounts a new drawer, and a
 * viewer who scrolled up to read back should still be there, not pulled to the beat's line.
 * It is a plain object the drawer writes as it scrolls (nothing redraws for it).
 */
import { useState } from 'react';
import { DEFAULT_FILTERS, type DrawerFilters } from './drawer-lines';

/** Where the drawer's lines are scrolled, and whether they follow the beat on stage. */
export interface DrawerScroll {
  following: boolean;
  top: number;
}

export function useDrawerFilters(initial: DrawerFilters = DEFAULT_FILTERS) {
  const [filters, setFilters] = useState<DrawerFilters>(initial);
  const [scroll] = useState<DrawerScroll>(() => ({ following: true, top: 0 }));
  return { filters, setFilters, scroll };
}
