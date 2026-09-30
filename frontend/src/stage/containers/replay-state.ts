/**
 * What the replay's viewer controls, as one reducer: where the cursor is, whether it is
 * playing and how fast, the X-ray, and what the right side of the stage holds. Kept pure (no
 * timers, no DOM) so a test can press the buttons; the theatre component holds the state and
 * runs the timer. The cursor moves only through transport.ts, and the slot's tabs and the X-ray
 * only through slot.ts, so this file decides nothing those two already decide.
 *
 * The X-ray is the one control that changes which beats exist (beat sheet §11), so the reducer
 * is made for a game's two beat lists and carries the cursor from one to the other.
 *
 * A preview (the landing's mini replay) is the same reducer with a `loop` window: the play runs
 * round the window instead of stopping, so there is no second player to keep in step. Its
 * buttons stay inside the window, and the X-ray carries the window across with the cursor.
 *
 * With the X-ray on, the play pauses at the stops (stops.ts: the night hub, the ballots in),
 * however it got there; the hub's notice visits a room, watches them all or ends the night.
 */
import type { SceneBeat } from '@/stage/beats/types';
import type { MotionSpeed, Presentation } from '@/stage/scenes/types';
import { pressFile, pressTranscript, pressXray, showFile } from '@/stage/slot';
import { afterNight, branchOf, endsRoom, hubOf, isStop } from './stops';
import {
  carryAcross,
  holdFor,
  jumpChapter,
  seekTo,
  stepBack,
  stepForward,
  still,
  type Cursor,
} from './transport';

export interface ReplayState {
  cursor: Cursor;
  playing: boolean;
  speed: MotionSpeed;
  xray: boolean;
  slot: Presentation['slot'];
  /**
   * A preview's window (the landing's mini replay): playing runs `from`..`to` and goes round
   * again, and a beat that waits for the viewer is played past. Null for the whole log.
   */
  loop: { from: number; to: number } | null;
  /**
   * The room the viewer went into by a tap on its seat (`day:actor`, stops.ts `branchOf`): when
   * its last step has played, the play rests there. Null once the cursor leaves it, or on play.
   */
  visit: string | null;
  /** Every room the cursor has been in (`day:actor`): the hub dims their seats. */
  visited: readonly string[];
}

export type ReplayAction =
  | { type: 'step'; dir: 1 | -1 }
  | { type: 'seek'; index: number }
  | { type: 'chapter'; dir: 1 | -1 }
  | { type: 'play' }
  | { type: 'pause' }
  | { type: 'toggle-play' }
  /** The beat's hold ran out while playing: on to the next. */
  | { type: 'tick' }
  | { type: 'speed'; speed: MotionSpeed }
  | { type: 'xray' }
  | { type: 'transcript' }
  | { type: 'file' }
  /** A seat tapped on the stage: its file comes to the pane (the seat is the theatre's). */
  | { type: 'show-file' }
  /**
   * A lit seat tapped (at the hub, or in another room): its room from its first step (the
   * spoke at `index`), played, resting on its last. The same seat again plays it again.
   */
  | { type: 'visit'; index: number }
  /** The night hub's "End the night": on to the first beat after the night whole, playing. */
  | { type: 'end-night' }
  /** A room's "Back to the night": that night's hub, still. */
  | { type: 'to-hub' };

export interface ReplayBeats {
  public: readonly SceneBeat[];
  xray: readonly SceneBeat[];
}

export function initialReplayState(slot: Presentation['slot'] = null): ReplayState {
  return {
    cursor: still(0),
    playing: false,
    speed: 'normal',
    xray: false,
    slot,
    loop: null,
    visit: null,
    visited: [],
  };
}

/**
 * A preview that plays one window of the public cut on a loop: no X-ray, no slot, the cursor
 * resting on `from`. The window is clamped to the list, so a short game still has one.
 */
export function initialLoopState(
  beats: readonly SceneBeat[],
  window: { from: number; to: number },
  opts: { playing: boolean; speed: MotionSpeed },
): ReplayState {
  const last = Math.max(0, beats.length - 1);
  const to = Math.min(Math.max(0, window.to), last);
  const from = Math.min(Math.max(0, window.from), to);
  return {
    cursor: still(from),
    playing: opts.playing,
    speed: opts.speed,
    xray: false,
    slot: null,
    loop: { from, to },
    visit: null,
    visited: [],
  };
}

/** A cursor a press moved outside the loop window lands on the window's nearer end, still. */
function inWindow(state: ReplayState): ReplayState {
  if (!state.loop) return state;
  const { from, to } = state.loop;
  const i = state.cursor.index;
  if (i >= from && i <= to) return state;
  return { ...state, cursor: still(i < from ? from : to) };
}

/**
 * Inside a loop window: past `to` the cursor goes back to `from`, still, and a beat that would
 * wait for the viewer is stepped past, so the loop never stops by itself. The guard stops the
 * play if every beat in the window waits (nothing would ever move).
 */
function looped(state: ReplayState, beats: readonly SceneBeat[]): ReplayState {
  const { from, to } = state.loop!;
  let cursor = state.cursor;
  for (let guard = 0; guard <= to - from + 1; guard++) {
    if (cursor.index < from || cursor.index > to) cursor = still(from);
    const beat = beats[cursor.index];
    if (!state.playing || !beat || holdFor(beat, state.speed) !== null)
      return { ...state, cursor };
    cursor = cursor.index >= to ? still(from) : stepForward(cursor, beats);
  }
  return { ...state, cursor, playing: false };
}

/** A beat that waits for the viewer (or the last beat) stops the play where it lands. */
function landed(state: ReplayState, beats: readonly SceneBeat[]): ReplayState {
  if (state.loop) return looped(state, beats);
  const beat = beats[state.cursor.index];
  const last = state.cursor.index >= beats.length - 1;
  if (!state.playing || !beat) return state;
  return last || holdFor(beat, state.speed) === null ? { ...state, playing: false } : state;
}

export function replayReducer(all: ReplayBeats) {
  const of = (xray: boolean) => (xray ? all.xray : all.public);
  /**
   * After every press: the rooms the cursor has been in are remembered, a visit ends when the
   * cursor leaves its room, and a cursor that has just arrived on a stop pauses the play there.
   */
  const settle = (was: ReplayState, now: ReplayState): ReplayState => {
    if (now.loop) return now;
    const beats = of(now.xray);
    const branch = branchOf(beats[now.cursor.index]);
    let s = now;
    if (s.visit && branch !== s.visit) s = { ...s, visit: null };
    if (branch && !s.visited.includes(branch))
      s = { ...s, visited: [...s.visited, branch] };
    const moved = now.cursor.index !== was.cursor.index || now.xray !== was.xray;
    if (moved && s.playing && isStop(beats, s.cursor.index, s.xray))
      s = { ...s, playing: false };
    return s;
  };
  return function reduce(state: ReplayState, action: ReplayAction): ReplayState {
    return settle(state, press(state, action));
  };
  function press(state: ReplayState, action: ReplayAction): ReplayState {
    const beats = of(state.xray);
    switch (action.type) {
      case 'step':
        return action.dir === 1
          ? landed({ ...state, cursor: stepForward(state.cursor, beats) }, beats)
          : inWindow({ ...state, cursor: stepBack(state.cursor) });
      case 'seek':
        return inWindow({ ...state, cursor: seekTo(action.index, beats) });
      case 'chapter':
        return inWindow({ ...state, cursor: jumpChapter(state.cursor, beats, action.dir) });
      case 'tick':
        if (!state.playing) return state;
        // a loop's last beat has held: round to the window's first, which arrives still
        if (state.loop && state.cursor.index >= state.loop.to)
          return landed({ ...state, cursor: still(state.loop.from) }, beats);
        {
          // a room visited by a tap has played its last step: it rests there (owner,
          // 2026-09-30; it returned to the hub by itself). "Back to the night" is the way back
          const here = beats[state.cursor.index];
          if (state.visit && endsRoom(here) && branchOf(here) === state.visit)
            return { ...state, playing: false };
        }
        return landed({ ...state, cursor: stepForward(state.cursor, beats) }, beats);
      case 'play': {
        if (beats.length === 0) return state;
        // play on from a visited room goes on through the night, as "Watch them all" does
        if (state.visit) return press({ ...state, visit: null }, action);
        if (state.loop) return landed({ ...state, playing: true }, beats);
        // at the end, play again from the top; on a beat that waits, playing moves on from it
        if (state.cursor.index >= beats.length - 1)
          return { ...state, playing: true, cursor: still(0) };
        const beat = beats[state.cursor.index];
        // a stop's ▶ ("Watch them all", "Count the votes") moves on from it at once
        if (
          holdFor(beat, state.speed) === null ||
          isStop(beats, state.cursor.index, state.xray)
        )
          return landed(
            { ...state, playing: true, cursor: stepForward(state.cursor, beats) },
            beats,
          );
        return { ...state, playing: true };
      }
      case 'pause':
        return { ...state, playing: false };
      case 'toggle-play':
        return press(state, { type: state.playing ? 'pause' : 'play' });
      case 'visit': {
        const b = beats[action.index];
        if (!b || state.loop) return state;
        return {
          ...state,
          cursor: { index: action.index, animate: true },
          playing: true,
          visit: branchOf(b),
        };
      }
      case 'end-night': {
        const b = beats[state.cursor.index];
        const next = b ? afterNight(beats, b.day) : -1;
        if (next < 0 || state.loop) return state;
        return landed({ ...state, cursor: still(next), playing: true, visit: null }, beats);
      }
      case 'to-hub': {
        const b = beats[state.cursor.index];
        const hub = b ? hubOf(beats, b.day) : -1;
        if (hub < 0 || state.loop) return state;
        return { ...state, cursor: still(hub), playing: false, visit: null };
      }
      case 'speed':
        return { ...state, speed: action.speed };
      case 'transcript':
        return { ...state, ...pressTranscript(state) };
      case 'file':
        return { ...state, ...pressFile(state) };
      case 'show-file':
        return { ...state, ...showFile(state) };
      case 'xray': {
        const next = pressXray(state);
        if (next.xray === state.xray) return { ...state, ...next };
        const [was, now] = [of(state.xray), of(next.xray)];
        const cursor = carryAcross(state.cursor, was, now);
        // a preview's window is carried by its two ends, which both lists hold
        const loop = state.loop && {
          from: carryAcross(still(state.loop.from), was, now).index,
          to: carryAcross(still(state.loop.to), was, now).index,
        };
        return { ...state, ...next, cursor, loop };
      }
    }
  }
}
