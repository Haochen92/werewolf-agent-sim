'use client';

/**
 * The replay player's stateful half: a cursor over the beats of a finished log, a timer
 * that advances it, and the controls a viewer has over both.
 *
 * The cursor counts revealed beats. It starts at the end, so a freshly opened replay shows
 * the whole game exactly as before; "play from start" rewinds it to zero and the timer
 * takes over. The timer waits the hold of the LAST revealed beat before showing the next,
 * so the viewer gets reading time for what is on screen, not for what is coming. Speed
 * divides the hold. A step, a skip or a jump moves the cursor directly and the timer
 * simply re-arms from wherever it landed.
 *
 * The folded view is the caller's: it folds the visible prefix. Refolding on every step is
 * a few hundred events and is nowhere near the cost of a paint.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import type { DurableGameEvent } from '@/types/contracts';
import {
  cursorAfterNextPhase,
  cursorAtDay,
  dayAtCursor,
  groupBeats,
  visibleEventCount,
  type Beat,
} from '@/game/replayPlayer';

export const SPEEDS = [1, 2, 4] as const;
export type Speed = (typeof SPEEDS)[number];

export interface ReplayPlayer {
  beats: Beat[];
  /** Revealed beats, 0..beats.length. */
  cursor: number;
  /** The log prefix the cursor reveals: fold this. */
  visibleEvents: DurableGameEvent[];
  /** Day of the last revealed beat; null before the first. */
  currentDay: number | null;
  playing: boolean;
  speed: Speed;
  /** True whenever the reveal is partial or the timer is running: the theater follows the cursor. */
  active: boolean;
  atEnd: boolean;
  playFromStart: () => void;
  play: () => void;
  pause: () => void;
  step: () => void;
  skipPhase: () => void;
  showAll: () => void;
  jumpToDay: (day: number) => void;
  setSpeed: (speed: Speed) => void;
}

export function useReplayPlayer(events: readonly DurableGameEvent[]): ReplayPlayer {
  const beats = useMemo(() => groupBeats(events), [events]);
  const [cursor, setCursor] = useState(beats.length);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState<Speed>(1);

  // A new log (the query resolving, or another game) opens fully revealed and paused.
  useEffect(() => {
    setCursor(beats.length);
    setPlaying(false);
  }, [beats]);

  useEffect(() => {
    if (!playing) return undefined;
    if (cursor >= beats.length) {
      setPlaying(false);
      return undefined;
    }
    const wait = cursor === 0 ? 0 : beats[cursor - 1].holdMs / speed;
    const timer = setTimeout(
      () => setCursor((current) => Math.min(current + 1, beats.length)),
      wait,
    );
    return () => clearTimeout(timer);
  }, [playing, cursor, beats, speed]);

  const clamp = useCallback(
    (value: number) => Math.max(0, Math.min(value, beats.length)),
    [beats.length],
  );

  const playFromStart = useCallback(() => {
    setCursor(0);
    setPlaying(true);
  }, []);
  const play = useCallback(() => {
    if (cursor >= beats.length) setCursor(0);
    setPlaying(true);
  }, [cursor, beats.length]);
  const pause = useCallback(() => setPlaying(false), []);
  const step = useCallback(() => setCursor((c) => clamp(c + 1)), [clamp]);
  const skipPhase = useCallback(
    () => setCursor((c) => cursorAfterNextPhase(beats, c)),
    [beats],
  );
  const showAll = useCallback(() => {
    setPlaying(false);
    setCursor(beats.length);
  }, [beats.length]);
  const jumpToDay = useCallback(
    (day: number) => setCursor(cursorAtDay(beats, day)),
    [beats],
  );

  const visibleEvents = useMemo(
    () => events.slice(0, visibleEventCount(beats, cursor)),
    [events, beats, cursor],
  );
  const atEnd = cursor >= beats.length;

  return {
    beats,
    cursor,
    visibleEvents,
    currentDay: dayAtCursor(beats, cursor),
    playing,
    speed,
    active: playing || !atEnd,
    atEnd,
    playFromStart,
    play,
    pause,
    step,
    skipPhase,
    showAll,
    jumpToDay,
    setSpeed,
  };
}
