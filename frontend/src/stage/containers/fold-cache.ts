/**
 * The log folded up to a beat, remembered. Every beat shows `fold(events.slice(0, end))`, and
 * a replay steps through a hundred-odd beats, so folding the whole log from the start at every
 * step would redo the same work each time. Instead each fold is kept by where it stopped, and
 * the next one starts from the nearest fold at or before it: stepping forward folds only the
 * events the new beat adds; stepping back (or seeking to a beat seen before) folds nothing.
 *
 * Safe to share because the fold never mutates a view: each event makes a new one.
 */
import { emptyGameView, foldEvent } from '@/game/foldEvents';
import type { FoldOptions, GameView } from '@/game/types';
import type { DurableGameEvent } from '@/types/contracts';

export interface FoldCache {
  /** The view of `events.slice(0, end)`. */
  at(end: number): GameView;
  /** How many events this cache has folded so far (what the tests check). */
  readonly folded: number;
}

export function createFoldCache(
  events: readonly DurableGameEvent[],
  options: FoldOptions = {},
): FoldCache {
  const views = new Map<number, GameView>([[0, emptyGameView(options)]]);
  let folded = 0;
  return {
    at(want) {
      const end = Math.max(0, Math.min(want, events.length));
      const hit = views.get(end);
      if (hit) return hit;
      let from = 0;
      for (const k of views.keys()) if (k <= end && k > from) from = k;
      let view = views.get(from)!;
      for (let i = from; i < end; i++) view = foldEvent(view, events[i], options);
      folded += end - from;
      views.set(end, view);
      return view;
    },
    get folded() {
      return folded;
    },
  };
}
