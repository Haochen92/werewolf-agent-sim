'use client';

/**
 * The replay theatre: a finished game played back on the stage, beat by beat (beat sheet §11,
 * handoff §5). This is the one place the replay's state lives: where the cursor is, whether it
 * plays and how fast, the X-ray, what the right side holds, and the drawer's filters and the
 * film's tab (kept here, above the scene, so they hold while the beats change under them).
 * Everything below it is drawn from props.
 *
 * Each beat is the log folded up to that beat, and the scene the beat names draws it. The
 * folds are remembered, so stepping forward folds only what the new beat adds.
 *
 * Playing is a timer on the beat's hold. A beat that waits for the viewer (the epilogue, the
 * curtain) stops the play there, and so does the end of the log. While a pointer or a finger
 * rests on a speech the hold pauses, and the clock picks up where it left off, so a long line
 * can be read to the end.
 *
 * `mini` makes it a preview (the landing's carriage): the same stage and the same reducer, with
 * no HUD, no side slot, no transport, no X-ray and no keys, playing one window of the public cut
 * round and round (`loop` in replay-state.ts). The frame around it is the caller's.
 */
import {
  useCallback,
  useEffect,
  useMemo,
  useReducer,
  useRef,
  useState,
  type PointerEvent,
} from 'react';
import { useReducedMotion } from 'motion/react';
import { castForGame } from '../cast/castForGame';
import { beatsFor } from '../beats/beatsFor';
import { useDrawerFilters } from '../drawer/use-drawer-filters';
import { StageMotion } from '../motion';
import type { MotionSpeed, Presentation, SlotInput } from '../scenes/types';
import { atRail, slotOf } from '../slot';
import { Stage } from '../Stage';
import { SCENES } from '../scenes';
import type { DurableGameEvent, ReplayGame } from '@/types/contracts';
import { createFoldCache } from './fold-cache';
import {
  initialLoopState,
  initialReplayState,
  replayReducer,
  type ReplayState,
} from './replay-state';
import { holdFor, transportLabel } from './transport';
import { TransportBand } from './TransportBand';
import styles from './ReplayTheatre.module.css';

export interface ReplayTheatreProps {
  game: Pick<ReplayGame, 'game_id' | 'events'>;
  /** A preview: no HUD, no slot, no band, no X-ray; plays `from`..`to` (indices into the
   *  public cut) on a loop when `autoplay`, else rests on `from`. The frame is the caller's. */
  mini?: { from: number; to: number; autoplay: boolean; speed?: MotionSpeed };
}

/** The replay has no seated human: the viewer is a spectator, or an observer with the X-ray. */
const ME = null;

/**
 * The drawer is open by default on a screen with room for it, closed on a phone (handoff §2).
 * A landscape phone is short; that is what tells it apart.
 */
function defaultSlot(): ReplayState['slot'] {
  if (typeof window === 'undefined') return null;
  return window.matchMedia('(max-height: 540px)').matches ? null : 'drawer';
}

/**
 * Runs `done` after `ms`, counting only while `running`: a pause (or a hand on the speech)
 * stops the clock and the rest of the wait carries over. A new `key` (another beat, another
 * speed) starts a fresh wait.
 */
function useHold(key: string, ms: number | null, running: boolean, done: () => void) {
  const left = useRef({ key: '', ms: 0 });
  useEffect(() => {
    if (!running || ms === null) return;
    if (left.current.key !== key) left.current = { key, ms };
    const since = Date.now();
    const t = setTimeout(done, left.current.ms);
    return () => {
      clearTimeout(t);
      left.current.ms = Math.max(0, left.current.ms - (Date.now() - since));
    };
  }, [key, ms, running, done]);
}

const isSpeech = (el: EventTarget | null) =>
  el instanceof Element && el.closest('[data-speech]') !== null;

export function ReplayTheatre({ game, mini }: ReplayTheatreProps) {
  const events = game.events as readonly DurableGameEvent[];
  const cast = useMemo(() => castForGame(game.game_id), [game.game_id]);
  const all = useMemo(
    () => ({
      public: beatsFor(events, { xray: false }),
      xray: beatsFor(events, { xray: true }),
    }),
    [events],
  );
  const reduce = useMemo(() => replayReducer(all), [all]);
  // a viewer who asked for less motion gets the preview at rest
  const stillPlease = useReducedMotion() === true;
  const autoplay = !!mini?.autoplay && !stillPlease;
  const [state, dispatch] = useReducer(reduce, undefined, () =>
    mini
      ? initialLoopState(all.public, mini, {
          playing: autoplay,
          speed: mini.speed ?? 'fast',
        })
      : initialReplayState(defaultSlot()),
  );
  // the preview's caller turns the play on and off (scrolled away, a phone held upright)
  const isMini = !!mini;
  useEffect(() => {
    if (isMini) dispatch({ type: autoplay ? 'play' : 'pause' });
  }, [isMini, autoplay]);
  const folds = useMemo(() => createFoldCache(events, { mySeat: ME }), [events]);
  const ahead = useMemo(() => folds.at(events.length), [folds, events.length]);

  const beats = state.xray ? all.xray : all.public;
  const index = Math.min(state.cursor.index, Math.max(0, beats.length - 1));
  const beat = beats[index];
  const view = useMemo(() => (beat ? folds.at(beat.end) : null), [folds, beat]);

  // the side slot's state that outlives a beat
  const drawer = useDrawerFilters();
  const [filmTab, setFilmTab] = useState('note');
  const { xrayOn } = drawer;
  const onXray = useCallback(() => {
    // turning the X-ray on brings the drawer's X-ray lines back on (handoff §2)
    if (!state.xray) xrayOn();
    dispatch({ type: 'xray' });
  }, [state.xray, xrayOn]);
  const slotInput = useMemo(
    (): SlotInput => ({
      filters: drawer.filters,
      onFilters: drawer.setFilters,
      filmTab,
      onFilmTab: setFilmTab,
      ahead,
      onTranscript: () => dispatch({ type: 'transcript' }),
      onXray,
      back: '/replays',
    }),
    [drawer.filters, drawer.setFilters, filmTab, ahead, onXray],
  );

  // playing: the beat's hold, paused while the speech is held
  const [held, setHeld] = useState(false);
  const tick = useCallback(() => dispatch({ type: 'tick' }), []);
  const hold = beat ? holdFor(beat, state.speed) : null;
  useHold(
    `${state.xray}:${index}:${state.speed}`,
    hold,
    state.playing && (isMini || !held),
    tick,
  );
  const onPointerOver = (e: PointerEvent) => setHeld(isSpeech(e.target));
  const onPointerOut = (e: PointerEvent) => setHeld(isSpeech(e.relatedTarget));
  // a beat change can take the speech out from under a resting pointer
  const root = useRef<HTMLDivElement>(null);
  useEffect(() => {
    setHeld(root.current?.querySelector('[data-speech]:hover') != null);
  }, [index, state.xray]);

  // the keys: arrows step, space plays or pauses, the brackets jump chapters (not a preview's)
  useEffect(() => {
    if (isMini) return;
    const onKey = (e: KeyboardEvent) => {
      const t = e.target as HTMLElement | null;
      if (t && (/^(INPUT|SELECT|TEXTAREA)$/.test(t.tagName) || t.isContentEditable)) return;
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const action =
        e.key === 'ArrowRight'
          ? ({ type: 'step', dir: 1 } as const)
          : e.key === 'ArrowLeft'
            ? ({ type: 'step', dir: -1 } as const)
            : e.key === ' '
              ? ({ type: 'toggle-play' } as const)
              : e.key === ']'
                ? ({ type: 'chapter', dir: 1 } as const)
                : e.key === '['
                  ? ({ type: 'chapter', dir: -1 } as const)
                  : null;
      if (!action) return;
      e.preventDefault();
      dispatch(action);
    };
    // a focused button would also take the space as a click on key-up: the key is ours
    const onKeyUp = (e: KeyboardEvent) => {
      if (e.key === ' ' && (e.target as HTMLElement | null)?.tagName === 'BUTTON')
        e.preventDefault();
    };
    window.addEventListener('keydown', onKey);
    window.addEventListener('keyup', onKeyUp);
    return () => {
      window.removeEventListener('keydown', onKey);
      window.removeEventListener('keyup', onKeyUp);
    };
  }, [isMini]);

  const presentation = useMemo(
    (): Presentation => ({
      xray: state.xray,
      slot: state.slot,
      motion: state.speed,
      hud: isMini ? 'none' : 'replay',
      cast,
      animate: state.cursor.animate,
    }),
    [state.xray, state.slot, state.speed, isMini, cast, state.cursor.animate],
  );

  const Scene = beat ? SCENES[beat.scene] : null;
  // the drawer runs to the foot of the stage (not on a prompt, not beside the epilogue)
  const besideDrawer =
    !!beat && slotOf(state) === 'drawer' && !atRail(beat) && beat.id !== 'over.epilogue';
  return (
    <div
      ref={root}
      className={styles.theatre}
      data-beat-index={index}
      data-beat={beat?.id}
      data-playing={state.playing}
      data-mini={isMini || undefined}
      onPointerOver={isMini ? undefined : onPointerOver}
      onPointerOut={isMini ? undefined : onPointerOut}
    >
      <Stage fit="contain">
        {beat && view && Scene ? (
          <StageMotion speed={state.speed}>
            <Scene
              view={view}
              beat={beat}
              me={ME}
              presentation={presentation}
              slot={slotInput}
            />
          </StageMotion>
        ) : null}
        {isMini ? null : (
          <TransportBand
            hud="replay"
            beats={beats}
            index={index}
            playing={state.playing}
            speed={state.speed}
            xray={state.xray}
            label={transportLabel(beats, index)}
            besideDrawer={besideDrawer}
            onChapter={(dir) => dispatch({ type: 'chapter', dir })}
            onStep={(dir) => dispatch({ type: 'step', dir })}
            onTogglePlay={() => dispatch({ type: 'toggle-play' })}
            onSeek={(i) => dispatch({ type: 'seek', index: i })}
            onSpeed={(speed) => dispatch({ type: 'speed', speed })}
          />
        )}
      </Stage>
    </div>
  );
}
