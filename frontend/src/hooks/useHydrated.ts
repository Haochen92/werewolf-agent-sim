'use client';
/**
 * False while React hydrates what the server drew, true after. A site page hydrates a moment
 * after the shell around it (it sits under the site's loading boundary, `(site)/loading.tsx`),
 * and in that moment a request the shell started can answer (the nav's count of the tables
 * boarding): a part that draws from it draws what the server drew first, its pending face, or
 * React finds the two disagree and draws the part again.
 */
import { useSyncExternalStore } from 'react';

const never = () => () => {};

export function useHydrated(): boolean {
  return useSyncExternalStore(
    never,
    () => true,
    () => false,
  );
}
