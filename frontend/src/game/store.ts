/**
 * The one client-side store: a single open game session (build_plan §4).
 *
 * It exists for a reason the reducer deliberately does not cover — **liveness**.
 * ux_journeys §0 makes this binding: beats (the role reveal, the game-over banner,
 * animations, sounds) fire on LIVE ARRIVAL ONLY. During any catch-up fold — refresh,
 * reconnect, replay scrub — events must render instantly in their settled form. The
 * reducer cannot tell the difference and must not try; the store carries the
 * live-vs-folded seq flag and the beat layer keys off it. That single rule is what makes
 * refresh-mid-game safe (D23).
 *
 * It ships from day one even though P1 (replay) only ever hydrates history: building the
 * flag in later would mean auditing every component that had already assumed liveness.
 *
 * Zustand rather than Context + useReducer because every SSE event writes here while
 * dozens of components subscribe — per-slice selectors keep that from becoming a
 * re-render storm, and the store is testable without React.
 */
import { create } from 'zustand';
import { liveSeen } from '@/lib/storage';
import type { DurableGameEvent, PhaseProgress } from '@/types/contracts';
import { emptyGameView, foldEvent, foldEvents } from './foldEvents';
import type { FoldOptions, GameView } from './types';

export type ConnectionState = 'idle' | 'connecting' | 'open' | 'reconnecting' | 'closed';

/** One pacing bar: `phase_progress` snapshots, monotonic-max applied (never moves backwards). */
export interface PacingBar {
  day: number;
  stage: PhaseProgress['stage'];
  done: number;
  total: number;
}

interface SessionState {
  gameId: string | null;
  view: GameView;
  /** The durable log as received — kept so an R7 backlog or a re-fold has its source. */
  events: DurableGameEvent[];
  /**
   * Seqs that arrived while this client was watching, as opposed to folded from history.
   * The ONLY consumer is the beat layer. Empty after a pure hydrate, which is exactly what
   * makes a refreshed mid-game session silent.
   */
  liveSeqs: Set<number>;
  /**
   * The newest seq that arrived as catch-up at the log's end (not a late insert like the
   * backlog after game over). After a reconnect this is where the missed events end, so the
   * stage lands on them still instead of playing them; 0 until anything has.
   */
  caughtUpTo: number;
  /**
   * The newest seq this tab had seen arrive live in this game before this connection
   * (`liveSeen`, read at hydrate); null when it never watched it live (a new tab, a late
   * arrival). What later came in as catch-up above it went by while the viewer was away: the
   * live theatre's "You're back" notice is built from it (`missedEvents`).
   */
  liveBefore: number | null;
  pacing: Record<string, PacingBar>;
  connection: ConnectionState;

  /** Fold a block of history. Marks nothing live — this is the catch-up path. */
  hydrate: (
    events: DurableGameEvent[],
    options?: FoldOptions & { gameId?: string },
  ) => void;
  /** Fold one event that just arrived on the wire. Marks it live — beats may fire. */
  applyLive: (event: DurableGameEvent) => void;
  /**
   * Fold a block of events that arrived as CATCH-UP, not as news. Marks nothing live.
   *
   * The SSE stream replays the log from the client's cursor before going live, and on a
   * first connection that cursor is 0 — so the entire history arrives through the same
   * socket as the future. Without this split, refreshing mid-game would re-fire the role
   * reveal and the game-over takeover for events that happened an hour ago, which is
   * exactly what ux_journeys §0 forbids. The boundary is the `last_seq` from the status
   * snapshot taken at connect time: at or below it is history, above it is news.
   *
   * A block, not one event: the stream gathers the catch-up frames that arrive together and
   * hands them in at once (`useGameStream`), so a long game's history is one store write and
   * one render instead of one per event, each over the whole log so far.
   */
  applyCatchUp: (events: readonly DurableGameEvent[]) => void;
  /** Ephemeral pacing snapshot; duplicates and stale values are harmless by design. */
  applyPacing: (progress: PhaseProgress) => void;
  /** Reconcile the folded request with the status snapshot, which owns whether it is active. */
  syncPending: (
    seat: string | null,
    pendingSeats: readonly string[],
    deadlines?: Readonly<Record<string, string>>,
    snapshotLastSeq?: number,
  ) => void;
  /** Clear immediately after an accepted/already-answered submit; the poll confirms later. */
  clearPending: () => void;
  setConnection: (connection: ConnectionState) => void;
  /** Name the seat this client owns (from GameStatus.you); re-folds so `me` resolves. */
  setMySeat: (seat: string | null) => void;
  reset: () => void;

  /** Did this seq arrive live? The beat layer's only question. */
  isLive: (seq: number) => boolean;
}

const pacingKey = (day: number, stage: PhaseProgress['stage']) => `${day}:${stage}`;

function normaliseEvents(events: readonly DurableGameEvent[]): DurableGameEvent[] {
  const bySeq = new Map(events.map((event) => [event.seq, event]));
  return [...bySeq.values()].sort((a, b) => a.seq - b.seq);
}

/** Whether a log sorted by seq holds `seq` (a binary search: the log can run to a thousand). */
function holds(events: readonly DurableGameEvent[], seq: number): boolean {
  let lo = 0;
  let hi = events.length - 1;
  while (lo <= hi) {
    const mid = (lo + hi) >> 1;
    const at = events[mid].seq;
    if (at === seq) return true;
    if (at < seq) lo = mid + 1;
    else hi = mid - 1;
  }
  return false;
}

/**
 * The log and the view with `arrived` added; null when every one of them was already there.
 * Every event has its seq, and the log is kept sorted by it, so whether an event belongs at
 * the end is a comparison, not a guess.
 */
function addDurable(
  view: GameView,
  events: DurableGameEvent[],
  arrived: readonly DurableGameEvent[],
): { events: DurableGameEvent[]; view: GameView } | null {
  const fresh = normaliseEvents(arrived).filter((event) => !holds(events, event.seq));
  if (fresh.length === 0) return null;
  const options = { mySeat: view.me.seat };
  // the usual case, live or catch-up: past the head, so the log grows at its end and the view
  // folds on from where it was
  if (fresh[0].seq > view.lastSeq) {
    let next = view;
    for (const event of fresh) next = foldEvent(next, event, options);
    return { events: events.concat(fresh), view: next };
  }
  // R7 deliberately breaks arrival order: `game_over` arrives first, then the server flushes
  // withheld observer events with older seqs. Incremental folding is valid only for an append;
  // an insertion must re-fold the sorted log or the reveal is either dropped or misordered.
  const nextEvents = normaliseEvents([...events, ...fresh]);
  return { events: nextEvents, view: foldEvents(nextEvents, options) };
}

const initial = {
  gameId: null,
  view: emptyGameView(),
  events: [] as DurableGameEvent[],
  liveSeqs: new Set<number>(),
  caughtUpTo: 0,
  liveBefore: null as number | null,
  pacing: {} as Record<string, PacingBar>,
  connection: 'idle' as ConnectionState,
};

export const useGameSession = create<SessionState>((set, get) => ({
  ...initial,

  hydrate: (events, options = {}) => {
    const { gameId, ...foldOptions } = options;
    const ordered = normaliseEvents(events);
    const game = gameId ?? get().gameId;
    set({
      gameId: game,
      events: ordered,
      view: foldEvents(ordered, foldOptions),
      // Deliberately NOT merged with any existing liveSeqs: a hydrate re-folds from
      // scratch, so every seq in the new view is history by definition.
      liveSeqs: new Set(),
      caughtUpTo: 0,
      // what this tab saw live before (a reload, a reconnect's new connection): kept per tab
      liveBefore: game ? liveSeen.get(game) : null,
      // Pacing is ephemeral and belongs to one connection. A re-hydrate/rejoin/new game
      // must not inherit a completed strip from the previous stream.
      pacing: {},
    });
  },

  applyCatchUp: (arrived) => {
    const { view, events } = get();
    const next = addDurable(view, events, arrived);
    if (!next) return;
    // liveSeqs untouched: this is history that arrived late. Where it ends, if it went past
    // the head (one at a time, the last to pass the head would be the newest: the same seq).
    const newest = next.view.lastSeq;
    set(newest > view.lastSeq ? { ...next, caughtUpTo: newest } : next);
  },

  applyLive: (event) => {
    const { view, events, liveSeqs } = get();
    const next = addDurable(view, events, [event]);
    // The server may re-send across a reconnect. Dedupe by membership, NOT by the current
    // high-water mark: the R7 reveal legitimately sends unseen lower seqs after game_over.
    if (!next) return;
    const nextLive = new Set(liveSeqs);
    nextLive.add(event.seq);
    const { gameId } = get();
    if (gameId) liveSeen.note(gameId, event.seq);
    set({
      ...next,
      liveSeqs: nextLive,
    });
  },

  applyPacing: (progress) => {
    const key = pacingKey(progress.day, progress.stage);
    const current = get().pacing[key];
    // Monotonic-max: snapshots can arrive out of order, and a bar that walks backwards
    // reads as a bug to the viewer even when the data is merely stale.
    if (current && current.done >= progress.done) return;
    set({
      pacing: {
        ...get().pacing,
        [key]: {
          day: progress.day,
          stage: progress.stage,
          done: progress.done,
          total: Math.max(progress.total, current?.total ?? 0),
        },
      },
    });
  },

  syncPending: (
    seat,
    pendingSeats,
    deadlines = {},
    snapshotLastSeq = Number.MAX_SAFE_INTEGER,
  ) => {
    const { view } = get();
    const pending = view.me.pending;
    const active = seat !== null && pendingSeats.includes(seat);
    if (!active) {
      // A status request and SSE race. Never let an older snapshot erase an input_request
      // whose seq was emitted after that snapshot's high-water mark.
      if (pending && pending.seq <= snapshotLastSeq) {
        set({ view: { ...view, me: { ...view.me, pending: null } } });
      }
      return;
    }
    if (!pending) return; // the matching input_request supplies action_kind + candidates
    const deadline = deadlines[seat] ?? pending.deadline;
    if (deadline !== pending.deadline) {
      set({
        view: { ...view, me: { ...view.me, pending: { ...pending, deadline } } },
      });
    }
  },

  clearPending: () => {
    const { view } = get();
    if (view.me.pending) set({ view: { ...view, me: { ...view.me, pending: null } } });
  },

  setConnection: (connection) => set({ connection }),

  /**
   * Name the seat this client owns, from `GameStatus.you`. Re-folds the log, because
   * `me.role` and `me.alive` are derived from the seat and every event already folded was
   * folded without knowing it. Cheap (the log is in memory) and far safer than patching
   * `me` in place and hoping nothing else depended on the seat.
   */
  setMySeat: (seat) => {
    const { view, events } = get();
    if (view.me.seat === seat) return;
    set({ view: foldEvents(events, { mySeat: seat }) });
  },

  reset: () =>
    set({
      ...initial,
      view: emptyGameView(),
      liveSeqs: new Set(),
      caughtUpTo: 0,
      liveBefore: null,
      pacing: {},
    }),

  isLive: (seq) => get().liveSeqs.has(seq),
}));

// --- selectors (subscribe to slices, not the whole store) --------------------

export const selectView = (s: SessionState) => s.view;
export const selectDay = (day: number) => (s: SessionState) => s.view.days[day];
export const selectConnection = (s: SessionState) => s.connection;
export const selectPending = (s: SessionState) => s.view.me.pending;
export const selectPacing =
  (day: number, stage: PhaseProgress['stage']) => (s: SessionState) =>
    s.pacing[pacingKey(day, stage)];
