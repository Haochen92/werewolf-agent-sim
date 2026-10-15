/**
 * The log folded up to a beat, remembered. Every beat shows `fold(events.slice(0, end))`, and
 * a replay steps through a hundred-odd beats, so folding the whole log from the start at every
 * step would redo the same work each time. Instead each fold is kept by where it stopped, and
 * the next one starts from the nearest fold at or before it: stepping forward folds only the
 * events the new beat adds; stepping back (or seeking to a beat seen before) folds nothing.
 *
 * Safe to share because the fold never mutates a view: each event makes a new one.
 *
 * A live game's log grows while the cache is in use: `grow` takes the longer log when it only
 * adds to the end of this one, so the folds already made (and the views the stage holds) stay.
 * A few dozen folds are kept, the oldest out (the empty view stays): a fold not kept is
 * folded again from the nearest one before it.
 */
import { emptyGameView, foldEvent } from '@/game/foldEvents';
import type { FoldOptions, GameView } from '@/game/types';
import type { DurableGameEvent } from '@/types/contracts';

export interface FoldCache {
  /** The view of `events.slice(0, end)`. */
  at(end: number): GameView;
  /**
   * Take a longer log, when it only adds to the end of this one (the same event objects up to
   * this one's length): true, and every fold made stays good. False, and nothing changes: the
   * caller makes a new cache (an event inserted before the end, a log started again).
   */
  grow(events: readonly DurableGameEvent[]): boolean;
  /** How many events this cache has folded so far (what the tests check). */
  readonly folded: number;
}

/** Folds kept besides the empty view: a replay's beats seen, a live game's latest. */
const KEEP = 96;

export function createFoldCache(
  initial: readonly DurableGameEvent[],
  options: FoldOptions = {},
): FoldCache {
  let events = initial;
  const views = new Map<number, GameView>([[0, emptyGameView(options)]]);
  let folded = 0;
  return {
    grow(longer) {
      const n = events.length;
      // the log is kept sorted by seq and its events are never copied, so an event inserted
      // before the end shifts the one at n - 1: one comparison tells an append from the rest
      if (longer.length < n || (n > 0 && longer[n - 1] !== events[n - 1])) return false;
      events = longer;
      return true;
    },
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
      if (views.size > KEEP + 1) {
        for (const k of views.keys())
          if (k !== 0) {
            views.delete(k);
            break;
          }
      }
      return view;
    },
    get folded() {
      return folded;
    },
  };
}
