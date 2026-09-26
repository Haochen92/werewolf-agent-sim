'use client';
/**
 * The games this browser sat in: every game id with a seat token in local storage
 * (`seatToken.all()`). Empty on the server and on the first client render, so the page hydrates
 * the same either way; it follows other tabs through the `storage` event.
 */
import { useMemo, useSyncExternalStore } from 'react';
import { seatToken } from '@/lib/storage';

function subscribe(onChange: () => void): () => void {
  window.addEventListener('storage', onChange);
  return () => window.removeEventListener('storage', onChange);
}

// a string snapshot: the store must return the same value while nothing changed
const snapshot = () => seatToken.all().sort().join('\n');
const serverSnapshot = () => '';

export function usePlayedHere(): ReadonlySet<string> {
  const ids = useSyncExternalStore(subscribe, snapshot, serverSnapshot);
  return useMemo(() => new Set(ids ? ids.split('\n') : []), [ids]);
}
