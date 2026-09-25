/**
 * What the replay's viewer controls, as one reducer: where the cursor is, whether it is
 * playing and how fast, the X-ray, and what the right side of the stage holds. Kept pure (no
 * timers, no DOM) so a test can press the buttons; the theatre component holds the state and
 * runs the timer. The cursor moves only through transport.ts, and the slot's two buttons only
 * through slot.ts, so this file decides nothing those two already decide.
 *
 * The X-ray is the one control that changes which beats exist (beat sheet §11), so the reducer
 * is made for a game's two beat lists and carries the cursor from one to the other.
 */
import type { SceneBeat } from '@/stage/beats/types';
import type { MotionSpeed, Presentation } from '@/stage/scenes/types';
import { pressTranscript, pressXray } from '@/stage/slot';
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
  | { type: 'transcript' };

export interface ReplayBeats {
  public: readonly SceneBeat[];
  xray: readonly SceneBeat[];
}

export function initialReplayState(slot: Presentation['slot'] = null): ReplayState {
  return { cursor: still(0), playing: false, speed: 'normal', xray: false, slot };
}

/** A beat that waits for the viewer (or the last beat) stops the play where it lands. */
function landed(state: ReplayState, beats: readonly SceneBeat[]): ReplayState {
  const beat = beats[state.cursor.index];
  const last = state.cursor.index >= beats.length - 1;
  if (!state.playing || !beat) return state;
  return last || holdFor(beat, state.speed) === null ? { ...state, playing: false } : state;
}

export function replayReducer(all: ReplayBeats) {
  const of = (xray: boolean) => (xray ? all.xray : all.public);
  return function reduce(state: ReplayState, action: ReplayAction): ReplayState {
    const beats = of(state.xray);
    switch (action.type) {
      case 'step':
        return action.dir === 1
          ? landed({ ...state, cursor: stepForward(state.cursor, beats) }, beats)
          : { ...state, cursor: stepBack(state.cursor) };
      case 'seek':
        return { ...state, cursor: seekTo(action.index, beats) };
      case 'chapter':
        return { ...state, cursor: jumpChapter(state.cursor, beats, action.dir) };
      case 'tick':
        if (!state.playing) return state;
        return landed({ ...state, cursor: stepForward(state.cursor, beats) }, beats);
      case 'play': {
        if (beats.length === 0) return state;
        // at the end, play again from the top; on a beat that waits, playing moves on from it
        if (state.cursor.index >= beats.length - 1)
          return { ...state, playing: true, cursor: still(0) };
        const beat = beats[state.cursor.index];
        if (holdFor(beat, state.speed) === null)
          return landed(
            { ...state, playing: true, cursor: stepForward(state.cursor, beats) },
            beats,
          );
        return { ...state, playing: true };
      }
      case 'pause':
        return { ...state, playing: false };
      case 'toggle-play':
        return reduce(state, { type: state.playing ? 'pause' : 'play' });
      case 'speed':
        return { ...state, speed: action.speed };
      case 'transcript':
        return { ...state, ...pressTranscript(state) };
      case 'xray': {
        const next = pressXray(state);
        if (next.xray === state.xray) return { ...state, ...next };
        const cursor = carryAcross(state.cursor, of(state.xray), of(next.xray));
        return { ...state, ...next, cursor };
      }
    }
  };
}
