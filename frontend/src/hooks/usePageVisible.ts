'use client';
/**
 * Whether the page is showing (`document.visibilityState`): false while the tab is in the
 * background, the window minimised or the phone locked. A replay's clock stops while it is
 * false and picks up where it left off, so a viewer who comes back finds the beat they left
 * rather than a game played on without them. The server render says visible.
 */
import { useSyncExternalStore } from 'react';

function subscribe(onChange: () => void) {
  document.addEventListener('visibilitychange', onChange);
  return () => document.removeEventListener('visibilitychange', onChange);
}

export function usePageVisible(): boolean {
  return useSyncExternalStore(
    subscribe,
    () => document.visibilityState !== 'hidden',
    () => true,
  );
}
