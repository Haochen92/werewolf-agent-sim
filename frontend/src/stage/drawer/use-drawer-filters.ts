'use client';

/**
 * The drawer's filters as state, for whoever mounts the stage (the workbench, the replay, the
 * live game). They live above the scenes because a scene is redrawn at every beat, and a
 * viewer who picked "Day 3" or one seat expects that to hold while the game plays on.
 *
 * `xrayOn` is what the container calls when the X-ray is switched on: the drawer's X-ray
 * lines come back on even if they were hidden before (handoff §2).
 */
import { useCallback, useState } from 'react';
import { DEFAULT_FILTERS, type DrawerFilters } from './drawer-lines';

export function useDrawerFilters(initial: DrawerFilters = DEFAULT_FILTERS) {
  const [filters, setFilters] = useState<DrawerFilters>(initial);
  const xrayOn = useCallback(
    () => setFilters((f) => ({ ...f, show: { ...f.show, xray: true } })),
    [],
  );
  return { filters, setFilters, xrayOn };
}
