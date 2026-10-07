'use client';

/**
 * The live theatre: a game being played, on the stage, as it happens (beat sheet §12, handoff
 * §6). This is the one place the live stage's state lives: which beat is on the stage, what
 * the right side holds, the drawer's filters and the film's tab, the seat's own card opened over
 * the stage from "your card" (it stays open while beats go by, until a tap or Esc), the seat
 * notebook's open editor (likewise, until Done, Esc, a tap outside or its seat's death), and the
 * seated human's open turn (the line being written, the drafts, what was sent). Everything
 * below it is drawn from props; the game itself comes from the session store, which the stream
 * fills.
 *
 * There is no transport. Beats play as events arrive: each new beat animates in and holds for
 * its time at normal speed, however many are queued (ruled 2026-10-01: the stage plays at
 * reading pace and lags the server), and history (a refresh, the page opened mid-game, what a
 * reconnect caught up on) lands still on the latest beat without playing anything; only a new
 * game's deal, which is always over before the page connects, plays from its first beat, and
 * on a page that watched its platform depart, the deal and everything after it play from the
 * first beat whatever the log already held. The rules are in live-state.ts; this file runs the
 * timer and talks to the server.
 *
 * The seated human's turn never waits for the stage: the clock runs on the request's real
 * deadline from the moment it arrives, and the beat on the stage is cut short once (the rest
 * keep their pace up to the prompt). Answers go out from whichever scene took them (the dock,
 * the ballot, the shelf room, the pack's chat) to one place here, which picks the right body
 * for the request and says what the server said.
 * A turn that runs out is answered by the seat's agent; that seat's own screen is told so
 * when its line arrives.
 *
 * After `game_over` every viewer holds the whole log, so the X-ray is on for everyone, from
 * the moment the stage reaches the ending (its first `over.*` beat; `game_over` can land while
 * the stage is still playing the last night, 2026-10-01): then the wing takes the truth, Reveal
 * and the seats' files unlock, and the ending plays to its curtain, whose way out goes to the
 * replay or back to the lobby. The replay is filed only when the engine's run ends (with
 * memory on, after the lessons are written, a minute or more after `game_over`): until the
 * archive answers for it, the curtain says "Winding the reels… come back in a few minutes"
 * where the link will be (`useReplayFiled`, 2026-10-01). Before the ending a seated player's
 * way out is the strip's door, which asks first ("Leave the table?") and goes to the lobby;
 * their agent plays on.
 *
 * Before the game, the same stage holds the waiting room: the platform (`StationScene`), drawn
 * from the room the page hands in (`room`), with the host's Lock and Depart going back out
 * through `onRoomAct`. When the host departs (or the status says the game has begun, for
 * everyone else) the train pulls out, a curtain falls on the empty platform, and it lifts on
 * the deal's first beat: one `<Stage>` throughout, so nothing remounts and nothing flashes.
 * Until the curtain is down the game's events are held back from the stage, so the deal
 * starts from its first beat behind it (beat sheet §1a).
 */
import { useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useReducer, useRef, useState } from 'react';
import { useGameSession, type PacingBar } from '@/game/store';
import { serverNow, useCountdown } from '@/hooks/useCountdown';
import { useLedger } from '@/hooks/useLedger';
import { useReplayFiled } from '@/hooks/useReplayFiled';
import { draftLine, rejoinGame, submitTurn, type TurnPayload } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { seatToken } from '@/lib/storage';
import { foldEvents } from '@/game/foldEvents';
import type { DurableGameEvent, GameStatus } from '@/types/contracts';
import { castForRoom, resolveCast } from '../cast/castForGame';
import { beatsFor } from '../beats/beatsFor';
import type { SceneBeat } from '../beats/types';
import { useDrawerFilters } from '../drawer/use-drawer-filters';
import { StageMotion } from '../motion';
import { notebookForAgent, useNotebook, useNoteEditing } from '../notebook';
import { CardOverlay } from '../instruments/FramedCard';
import { LeaveConfirm } from '../instruments/TopStrip';
import { draftRequest } from '../instruments/turn-dock';
import { seatNumber } from '../roles';
import { SCENES } from '../scenes';
import { capsNote } from '../scenes/ShelfRoomScene';
import { StationScene } from '../scenes/StationScene';
import { CURTAIN, DEPART, stationBeat, stationBeatId } from '../scenes/station';
import type {
  DockInput,
  Presentation,
  RoomAct,
  RoomInput,
  SlotInput,
  TurnInput,
} from '../scenes/types';
import { sideOpen } from '../slot';
import { Layer, Stage } from '../Stage';
import { geometry } from '../units';
import { createFoldCache } from './fold-cache';
import {
  actSent,
  curtainReplay,
  historyEnd as historyEndOf,
  historyLanding,
  initialLiveState,
  initialTurnState,
  liveReducer,
  payloadFor,
  requestBefore,
  requestIsActive,
  seesXray,
  turnClock,
  turnReducer,
  type Answer,
  type LiveCtx,
} from './live-state';
import { holdFor } from './transport';
import { memoryOn, type FileChoice } from '../film/case-file';
import type { RecordPick } from '../film/record-model';
import styles from './LiveTheatre.module.css';

export interface LiveTheatreProps {
  /** The full uuid: the cast is drawn from it. */
  gameId: string;
  /** The status poll's latest answer: whose turns are pending, and up to where it saw. */
  status: GameStatus | undefined;
  /** The waiting room, while the status says `waiting`: the stage shows the platform. */
  room?: RoomInput;
  /** The host's Depart went through: the train leaves before the status has caught up. */
  departed?: boolean;
  /** The host's presses on the platform's ledge. */
  onRoomAct?: (act: RoomAct) => void;
}

/**
 * Where the waiting room is in its hand-off to the game: not on the stage (`off`, a page opened
 * on a game already under way, or once the deal has taken over), waiting, the train leaving,
 * the curtain falling on the empty platform, and the curtain lifting off the deal.
 */
type Platform = 'off' | 'waiting' | 'departing' | 'closing' | 'opening';

const NO_EVENTS: readonly DurableGameEvent[] = [];
const EMPTY_VIEW = foldEvents([]);

/** The departure's length: the whole of it, or a moment for a viewer who asked for less motion. */
function departMs(): number {
  const reduce =
    typeof window !== 'undefined' &&
    window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
  return reduce ? 600 : DEPART.total * 1000;
}

/** The lobby: where the curtain's "Back to the lobby" and the strip's door go. */
const LOBBY = '/rooms';

/** The drawer is open by default on a screen with room for it (as the replay's). */
function defaultSlot(): Presentation['slot'] {
  if (typeof window === 'undefined') return null;
  return window.matchMedia('(max-height: 540px)').matches ? null : 'drawer';
}

/** The live count for a beat's pill: the ballots in (the vote), the acts in (the night). */
function progressFor(
  beat: SceneBeat,
  pacing: Record<string, PacingBar>,
): TurnInput['progress'] {
  // the night's count also reaches the seat's own room and the pack's, once their act is in
  const night = beat.scene === 'night' || beat.scene === 'room' || beat.scene === 'pack';
  const stage = beat.scene === 'vote' ? 'day_vote' : night ? 'night' : null;
  const bar = stage ? pacing[`${beat.day}:${stage}`] : undefined;
  return bar ? { n: bar.done, total: bar.total } : undefined;
}

/** A 403 means the seat cookie was lost: win it back with the stored token, then try once more. */
async function asSeat<T>(gameId: string, call: () => Promise<T>): Promise<T> {
  try {
    return await call();
  } catch (err) {
    if (!(err instanceof ApiError) || !err.isSeatLost) throw err;
    const token = seatToken.get(gameId);
    if (!token) throw err;
    try {
      await rejoinGame(gameId, token);
    } catch (rejoinError) {
      seatToken.clear(gameId);
      throw rejoinError;
    }
    return call();
  }
}

const failure = (err: unknown) => ({
  status: err instanceof ApiError ? err.status : 0,
  // the server's own words for a refusal; a dropped connection gets plain ones
  message: err instanceof ApiError ? err.message : 'Could not reach the table. Try again.',
});

export function LiveTheatre({
  gameId,
  status,
  room,
  departed = false,
  onRoomAct,
}: LiveTheatreProps) {
  const queryClient = useQueryClient();
  const storeGame = useGameSession((s) => s.gameId);
  const storeEvents = useGameSession((s) => s.events);
  const view = useGameSession((s) => s.view);
  const liveSeqs = useGameSession((s) => s.liveSeqs);
  const caughtUpTo = useGameSession((s) => s.caughtUpTo);
  const pacing = useGameSession((s) => s.pacing);
  const connection = useGameSession((s) => s.connection);
  const clearPending = useGameSession((s) => s.clearPending);

  // --- the waiting room, and its hand-off to the deal -------------------------------
  const [platform, setPlatform] = useState<Platform>(() => (room ? 'waiting' : 'off'));
  const [curtainDown, setCurtainDown] = useState(false);
  // the room as it last was: the train leaves with the people who were aboard
  const [heldRoom, setHeldRoom] = useState(room);
  useEffect(() => {
    if (room) setHeldRoom(room);
  }, [room]);
  // what the platform first showed lands still; after that, what changes on it moves
  const [platformSeen, setPlatformSeen] = useState(false);
  // the train left on this page: the deal, and whatever followed it, play from the first beat
  const [departedHere, setDepartedHere] = useState(false);
  useEffect(() => {
    if (platform !== 'off') setPlatformSeen(true);
    if (platform === 'departing') setDepartedHere(true);
  }, [platform]);
  const begun = status !== undefined && status.state !== 'waiting';
  useEffect(() => {
    if (platform === 'waiting' && (departed || begun)) setPlatform('departing');
  }, [platform, departed, begun]);
  useEffect(() => {
    const after = (ms: number, then: () => void) => {
      const t = setTimeout(then, ms);
      return () => clearTimeout(t);
    };
    if (platform === 'departing') return after(departMs(), () => setPlatform('closing'));
    if (platform === 'closing')
      return after(CURTAIN.close * 1000, () => setCurtainDown(true));
    if (platform === 'opening') return after(CURTAIN.open * 1000, () => setPlatform('off'));
  }, [platform]);
  // the game reaches the stage once the curtain is down on the platform, so the deal starts
  // from its first beat behind it; a stale log from another game never reaches it
  const fed =
    platform === 'off' || platform === 'opening' || (platform === 'closing' && curtainDown);
  const events = fed && storeGame === gameId ? storeEvents : NO_EVENTS;

  const me = view.me.seat;
  // after game over the whole log is everyone's: every viewer is an observer (what the viewer
  // sees of it waits for the stage to reach the ending: `xrayShown`, below)
  const xray = view.winner !== null;
  // a waiting room wears its picks on the platform; the dealt game wears the recorded cast
  const picks =
    status?.state === 'waiting' ? JSON.stringify(status.characters ?? []) : null;
  const cast = useMemo(
    () =>
      picks !== null
        ? castForRoom(JSON.parse(picks) as (string | null)[], gameId)
        : resolveCast(status?.cast, gameId),
    [picks, status?.cast, gameId],
  );
  const beats = useMemo(
    () => beatsFor(events, { xray, me, live: true }),
    [events, xray, me],
  );
  const historyEnd = useMemo(
    () => historyEndOf(events, liveSeqs, caughtUpTo),
    [events, liveSeqs, caughtUpTo],
  );
  // how far the log had got when the page connected (for a waiting room: when the game began,
  // which is when the stream opened): the history is all in once it gets there
  const [connectedAt, setConnectedAt] = useState<number | null>(() =>
    begun ? (status?.last_seq ?? 0) : null,
  );
  if (connectedAt === null && begun) setConnectedAt(status?.last_seq ?? 0);
  const landing = useMemo(
    () =>
      connectedAt === null
        ? 'pending'
        : historyLanding(events, historyEnd, connectedAt, departedHere),
    [events, historyEnd, connectedAt, departedHere],
  );
  const folds = useMemo(() => createFoldCache(events, { mySeat: me }), [events, me]);

  // --- the seated human's turn ---------------------------------------------------
  const pending = view.me.pending;
  const [turn, turnDispatch] = useReducer(turnReducer, initialTurnState);
  const pendingSeq = pending?.seq ?? null;
  useEffect(() => {
    if (pendingSeq !== null) turnDispatch({ type: 'open', seq: pendingSeq });
  }, [pendingSeq]);

  // when each request arrived live, in server time: the clock's whole runs from there
  const arrivals = useRef(new Map<number, number>());
  const [arrivedAt, setArrivedAt] = useState<number | null>(null);
  useEffect(() => {
    if (pendingSeq === null) return;
    if (liveSeqs.has(pendingSeq) && !arrivals.current.has(pendingSeq))
      arrivals.current.set(pendingSeq, serverNow());
    setArrivedAt(arrivals.current.get(pendingSeq) ?? null);
  }, [pendingSeq, liveSeqs]);

  const mine = turn.seq !== null && turn.seq === pendingSeq;
  // a draft credits its wait back to the clock: its deadline is the newer one
  const deadline =
    mine && turn.deadline !== undefined ? turn.deadline : (pending?.deadline ?? null);
  const countdown = useCountdown(deadline);
  const active = requestIsActive(pending, me, status) && view.me.alive && !xray;
  const open = active && mine && !turn.answered && !countdown.expired;
  useEffect(() => {
    // run out with no answer from here: the seat's agent answers it
    if (active && mine && countdown.expired && pendingSeq !== null)
      turnDispatch({ type: 'expired', seq: pendingSeq });
  }, [active, mine, countdown.expired, pendingSeq]);

  const refresh = useCallback(
    () => queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) }),
    [queryClient, gameId],
  );

  const send = useCallback(
    async (payload: TurnPayload, seq: number) => {
      const delegated = 'delegate' in payload;
      turnDispatch({ type: 'sending', seq });
      try {
        await asSeat(gameId, () => submitTurn(gameId, payload));
        turnDispatch({ type: 'sent', seq, delegated });
        clearPending();
      } catch (err) {
        const f = failure(err);
        turnDispatch({ type: 'send-failed', seq, ...f });
        // already answered (by the agent on the deadline, or a second press): let it go
        if (f.status === 409) clearPending();
      } finally {
        refresh();
      }
    },
    [gameId, clearPending, refresh],
  );

  const answer = useCallback(
    (a: Answer) => {
      if (!pending || !mine || turn.answered || turn.sending) return;
      const payload = payloadFor(pending, a);
      if (payload) void send(payload, pending.seq);
    },
    [pending, mine, turn.answered, turn.sending, send],
  );
  const onSay = useCallback((text: string) => answer({ say: text }), [answer]);
  const onAct = useCallback((target: string | null) => answer({ act: target }), [answer]);
  const onDelegate = useCallback(() => answer({ delegate: true }), [answer]);

  // The seat notebook goes with a draft only while "Use my seat notes" is ticked; a dead
  // seat's suspect mark is dropped, as the rail drops it.
  const book = useNotebook(me ? gameId : null);
  const notebook = useMemo(
    () => notebookForAgent(book, (n) => !view.alive.includes(`player_${n}`)),
    [book, view.alive],
  );
  const onDraft = useCallback(
    // the seat's own agent writes its line; the notes steer it and revise the line in the box
    async (notes: string, current: string) => {
      if (pendingSeq === null) return;
      const seq = pendingSeq;
      turnDispatch({ type: 'drafting', seq });
      const body = draftRequest(notes, current, notebook, turn.shareNotebook);
      try {
        const r = await asSeat(gameId, () => draftLine(gameId, body));
        turnDispatch({
          type: 'drafted',
          seq,
          draft: r.draft,
          draftsLeft: r.drafts_left,
          deadline: r.deadline ?? null,
        });
      } catch (err) {
        const f = failure(err);
        turnDispatch({ type: 'draft-failed', seq, ...f });
        if (f.status === 409) refresh();
      }
    },
    [gameId, pendingSeq, refresh, turn.shareNotebook, notebook],
  );

  // --- the stage -----------------------------------------------------------------
  const rolesLanded = Object.keys(view.xray.roles).length > 0;
  const openPrompt = open ? pendingSeq : null;
  const byAgent = turn.byAgent;
  const ctx = useMemo(
    (): LiveCtx => ({ me, rolesLanded, openPrompt, byAgent }),
    [me, rolesLanded, openPrompt, byAgent],
  );
  const ctxRef = useRef(ctx);
  useEffect(() => {
    ctxRef.current = ctx;
  }, [ctx]);

  const [state, dispatch] = useReducer(liveReducer, undefined, () =>
    initialLiveState(defaultSlot()),
  );
  // every change to the log, or to what the stage may be waiting for, is a new cut
  useEffect(() => {
    dispatch({ type: 'recut', beats, historyEnd, landing, ctx });
  }, [beats, historyEnd, landing, ctx]);

  const index = state.cursor.index;
  const beat: SceneBeat | undefined = state.beats[index];
  // the X-ray as the viewer has it: on once the stage has reached the ending, not before
  const xrayShown = seesXray(state, xray);
  const holdMs = beat && state.holding ? holdFor(beat, state.speed) : null;
  useEffect(() => {
    if (holdMs === null) return;
    const step = state.step;
    const t = setTimeout(
      () => dispatch({ type: 'held', step, ctx: ctxRef.current }),
      holdMs,
    );
    return () => clearTimeout(t);
  }, [state.step, holdMs]);

  // the side slot's state that outlives a beat; the game's end is the X-ray's switch here
  const drawer = useDrawerFilters();
  // the seat's own card, opened over the stage from "your card": it stays open as beats go by
  const [cardOpen, setCardOpen] = useState(false);
  useEffect(() => {
    if (!cardOpen) return;
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setCardOpen(false);
    window.addEventListener('keydown', esc);
    return () => window.removeEventListener('keydown', esc);
  }, [cardOpen]);
  const [filmTab, setFilmTab] = useState('notes');
  const [fileSeat, setFileSeat] = useState<FileChoice | null>(null);
  const [recordPick, setRecordPick] = useState<RecordPick | null>(null);
  // the claim ledger for the file's Record (public, so from the first morning): asked again
  // each time a new day begins, which is a new morning's ledger
  const morning =
    storeGame === gameId
      ? view.timeline.reduce((m, t) => (t.phase === 'day' ? Math.max(m, t.day) : m), 0)
      : 0;
  const ledger = useLedger(gameId, morning);
  // the seat notebook's open editor: it stays open while beats and scenes go by
  const noteEditing = useNoteEditing();
  // the strip's door: "Leave the table?" is open (a seated player, until the game ends)
  const [leaving, setLeaving] = useState(false);
  const router = useRouter();
  const ahead = useMemo(
    () => (xrayShown ? folds.at(events.length) : null),
    [xrayShown, folds, events.length],
  );
  // the replay is filed when the run ends (with memory on, after the lessons): until the
  // archive answers for it, the curtain's way to it is a plaque
  const archived = !!status?.archived;
  const answered = useReplayFiled(gameId, xray && !archived);
  const toReplay = curtainReplay(gameId, {
    archived,
    answered,
    memory: memoryOn(view),
    taught: view.xray.extracted !== null,
  });
  const slotInput = useMemo(
    (): SlotInput => ({
      filters: drawer.filters,
      onFilters: drawer.setFilters,
      drawerScroll: drawer.scroll,
      filmTab,
      onFilmTab: setFilmTab,
      fileSeat,
      onFileSeat: setFileSeat,
      ledger,
      recordPick,
      onRecordPick: setRecordPick,
      onShowRecord: () => dispatch({ type: 'show-record' }),
      notebook: noteEditing,
      // the closed file's way to the thinking turn by turn (the curtain's "Watch the replay"),
      // once the replay is filed
      replayHref: toReplay.replay ?? undefined,
      ahead,
      onTranscript: () => dispatch({ type: 'transcript' }),
      // the file opens any time: until the game's end it holds the Record alone
      onFile: () => dispatch({ type: 'file' }),
      onOpenFile: (seat) => {
        setFileSeat({ seat, key: null });
        dispatch({ type: 'show-file', xray: xrayShown });
      },
      // Reveal is locked until the stage reaches the game's end, then on for good
      revealLocked: !xrayShown,
      // a seated player's way out, until the game's end brings the curtain's
      onLeave: me && !xrayShown ? () => setLeaving(true) : undefined,
    }),
    [
      drawer.filters,
      drawer.setFilters,
      drawer.scroll,
      filmTab,
      fileSeat,
      ledger,
      recordPick,
      noteEditing,
      ahead,
      xrayShown,
      toReplay.replay,
      me,
    ],
  );

  const presentation = useMemo(
    (): Presentation => ({
      xray: xrayShown,
      slot: state.slot,
      motion: state.speed,
      hud: 'live',
      cast,
      animate: state.cursor.animate,
      game: gameId,
    }),
    [xrayShown, state.slot, state.speed, cast, state.cursor.animate, gameId],
  );

  const sceneView = useMemo(() => (beat ? folds.at(beat.end) : null), [folds, beat]);
  const clock = open && pending ? turnClock(deadline, arrivedAt) : null;
  const dock: DockInput | undefined =
    beat?.id === 'day.your-turn'
      ? {
          text: turn.text,
          round: pending?.round ?? null,
          onText: (text) => turnDispatch({ type: 'text', text }),
          notes: turn.notes,
          onNotes: (notes) => turnDispatch({ type: 'notes', notes }),
          onDraft,
          notebook: notebook
            ? {
                shared: turn.shareNotebook,
                onShared: (share) => turnDispatch({ type: 'share-notebook', share }),
              }
            : undefined,
          draftsLeft: turn.draftsLeft,
          drafting: turn.drafting,
          sending: turn.sending,
          error: turn.error,
          closed: !(open && beat.seq === pendingSeq),
        }
      : undefined;
  const agentSpoke =
    beat?.id === 'day.speech' && beat.subject === me && me !== null
      ? turn.byAgent.includes(requestBefore(events, beat.seq, me) ?? -1)
      : false;
  // the kill decided on the night this seat was asked for its vote: how that vote went in
  const votedTonight =
    beat?.id === 'pack.decided' &&
    events.some(
      (e) =>
        e.seq === turn.seq &&
        e.type === 'input_request' &&
        e.action_kind === 'wolf_vote' &&
        e.day === beat.day,
    );
  const turnInput: TurnInput | undefined = beat
    ? {
        clock: beat.liveOnly && beat.seq === pendingSeq ? clock : null,
        // the night room's plate seals once its act is in, and reopens if the send failed
        ...(beat.liveOnly && beat.seq === turn.seq ? actSent(turn) : {}),
        ...(votedTonight ? { sent: actSent(turn).sent } : {}),
        progress: progressFor(beat, pacing),
        agentSpoke,
        dock,
        onCard: () => setCardOpen(true),
      }
    : undefined;
  const myRole = me ? (view.me.role?.role ?? null) : null;

  // the curtain is down and the deal's first beat is on the stage under it: lift it
  useEffect(() => {
    if (platform === 'closing' && curtainDown && beat) setPlatform('opening');
  }, [platform, curtainDown, beat]);

  const Scene = beat ? SCENES[beat.scene] : null;
  const platformOn = platform !== 'off' && heldRoom !== undefined;
  const liveOn = platform === 'off' || platform === 'opening';
  const stationId = stationBeatId(heldRoom ?? { locked: false }, platform !== 'waiting');
  const stationPresentation: Presentation = {
    xray: false,
    slot: null,
    motion: 'normal',
    hud: 'live',
    cast,
    animate: platformSeen,
  };
  // a prompt that is not the day's dock (the ballot, a night act, the pack): the agent can take it
  const handOver = open && beat?.liveOnly && beat.id !== 'day.your-turn';
  return (
    <div
      className={styles.theatre}
      data-beat-index={index}
      data-beat={liveOn ? beat?.id : stationId}
      data-platform={platform}
      data-holding={state.holding}
      data-open-prompt={openPrompt ?? undefined}
    >
      <Stage fit="contain">
        {platformOn ? (
          <StationScene
            view={EMPTY_VIEW}
            beat={stationBeat(stationId)}
            me={null}
            presentation={stationPresentation}
            room={{
              ...heldRoom,
              curtain:
                platform === 'closing'
                  ? 'closing'
                  : platform === 'opening'
                    ? 'opening'
                    : null,
            }}
            onAct={(act) => onRoomAct?.(act as RoomAct)}
          />
        ) : null}
        {liveOn && beat && sceneView && Scene ? (
          <StageMotion speed={state.speed}>
            <Scene
              view={sceneView}
              beat={beat}
              me={me}
              presentation={presentation}
              slot={slotInput}
              turn={turnInput}
              onAct={onAct}
              onSay={onSay}
              // a tap on the speech box: this page is read, end its hold
              onNext={() =>
                dispatch({ type: 'held', step: state.step, ctx: ctxRef.current })
              }
              wayOut={{ ...toReplay, lobby: LOBBY }}
            />
          </StageMotion>
        ) : null}
        <Layer name="hud">
          {!beat && !platformOn ? (
            <p className={styles.waiting}>The table is being seated…</p>
          ) : null}
          {beat?.id === 'over.epilogue' ? (
            <button
              type="button"
              className={styles.onward}
              onClick={() => dispatch({ type: 'dismiss', ctx: ctxRef.current })}
            >
              Close the sheet
            </button>
          ) : null}
          {handOver ? (
            <button
              type="button"
              className={styles.handOver}
              onClick={onDelegate}
              disabled={turn.sending}
            >
              Let my agent play this turn
            </button>
          ) : null}
          {handOver && turn.error ? (
            <p className={styles.error} role="alert">
              {turn.error}
            </p>
          ) : null}
          {liveOn && cardOpen && me && myRole ? (
            <CardOverlay
              role={myRole}
              seat={seatNumber(me)}
              u={geometry('live', sideOpen(presentation)).u * 1.6}
              alone={myRole === 'wolf' && !view.packRoster.some((s) => s !== me)}
              note={capsNote(view.me.role?.bullets ?? null)}
              onClose={() => setCardOpen(false)}
            />
          ) : null}
          {liveOn && beat && leaving && me && !xrayShown ? (
            <LeaveConfirm
              hud="live"
              side={sideOpen(presentation)}
              onStay={() => setLeaving(false)}
              onLeave={() => router.push(LOBBY)}
            />
          ) : null}
          {connection === 'reconnecting' ? (
            <p className={styles.connection} data-connection>
              Reconnecting…
            </p>
          ) : null}
        </Layer>
      </Stage>
    </div>
  );
}
