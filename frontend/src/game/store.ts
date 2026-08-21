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
  pacing: Record<string, PacingBar>;
  connection: ConnectionState;

  /** Fold a block of history. Marks nothing live — this is the catch-up path. */
  hydrate: (
    events: DurableGameEvent[],
    options?: FoldOptions & { gameId?: string },
  ) => void;
  /** Fold one event that just arrived on the wire. Marks it live — beats may fire. */
  applyLive: (event: DurableGameEvent) => void;
  /** Ephemeral pacing snapshot; duplicates and stale values are harmless by design. */
  applyPacing: (progress: PhaseProgress) => void;
  setConnection: (connection: ConnectionState) => void;
  reset: () => void;

  /** Did this seq arrive live? The beat layer's only question. */
  isLive: (seq: number) => boolean;
}

const pacingKey = (day: number, stage: PhaseProgress['stage']) => `${day}:${stage}`;

const initial = {
  gameId: null,
  view: emptyGameView(),
  events: [] as DurableGameEvent[],
  liveSeqs: new Set<number>(),
  pacing: {} as Record<string, PacingBar>,
  connection: 'idle' as ConnectionState,
};

export const useGameSession = create<SessionState>((set, get) => ({
  ...initial,

  hydrate: (events, options = {}) => {
    const { gameId, ...foldOptions } = options;
    set({
      gameId: gameId ?? get().gameId,
      events,
      view: foldEvents(events, foldOptions),
      // Deliberately NOT merged with any existing liveSeqs: a hydrate re-folds from
      // scratch, so every seq in the new view is history by definition.
      liveSeqs: new Set(),
    });
  },

  applyLive: (event) => {
    const { view, events, liveSeqs } = get();
    // The server may re-send across a reconnect (Last-Event-ID replays from the cursor);
    // folding the same seq twice would duplicate transcript slots.
    if (event.seq <= view.lastSeq) return;
    const nextLive = new Set(liveSeqs);
    nextLive.add(event.seq);
    set({
      events: [...events, event],
      view: foldEvent(view, event, { mySeat: view.me.seat }),
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

  setConnection: (connection) => set({ connection }),

  reset: () => set({ ...initial, view: emptyGameView(), liveSeqs: new Set(), pacing: {} }),

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
