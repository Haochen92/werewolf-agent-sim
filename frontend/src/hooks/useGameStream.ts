'use client';

/**
 * The live wire: snapshot, then stream (build_plan §5).
 *
 *   1. GET /games/{id} seeds status — state, `you`, `last_seq`, deadlines.
 *   2. EventSource(/games/{id}/events?last_seq=N) carries two frame kinds: `game`
 *      (durable, folded) and `pacing` (ephemeral, monotonic-max).
 *   3. A status poll runs alongside while the game is running. It is not redundant: a dead
 *      game task emits NO stream signal — heartbeats keep flowing and `state` stays
 *      "running" — so the poll's `error` field is the ONLY way to detect it.
 *
 * The load-bearing subtlety is the catch-up boundary. The stream replays the log from the
 * client's cursor before going live, and on a first connection that cursor is 0 — so the
 * entire history arrives through the same socket as the future. Everything at or below the
 * snapshot's `last_seq` is folded as HISTORY, in blocks of the frames that arrive together
 * (`catchUpBatch`); only what is above it counts as news and can fire a beat. Without that split, every refresh would replay the role reveal and the
 * game-over takeover for events that happened an hour ago (ux_journeys §0, D23). A reconnect
 * moves the boundary on to what it caught up on (catch-up-boundary.ts).
 *
 * When the page comes back (shown again, or back online) and the stream is not open, it is
 * reopened at once from where the page has got to, instead of waiting on the browser's own
 * retry; what it then sends is a reconnect's catch-up like any other (2026-10-11).
 */
import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiUrl } from '@/lib/config';
import { getGameStatus } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { useGameSession } from '@/game/store';
import { catchUpBatch, catchUpBoundary, reopenNow } from './catch-up-boundary';
import { recordServerClock } from './useCountdown';
import type {
  DurableGameEvent,
  GameState,
  GameStatus,
  PhaseProgress,
} from '@/types/contracts';

export interface GameStream {
  status: GameStatus | undefined;
  state: GameState | undefined;
  /** Set only when the game task died; the stream cannot tell you this (D23). */
  error: string | null;
  /** Failure to obtain the status snapshot itself (404, invalid cookie, network, proxy). */
  statusError: Error | null;
  isPending: boolean;
}

export function useGameStream(gameId: string, enabled = true): GameStream {
  const hydrate = useGameSession((s) => s.hydrate);
  const applyLive = useGameSession((s) => s.applyLive);
  const applyCatchUp = useGameSession((s) => s.applyCatchUp);
  const applyPacing = useGameSession((s) => s.applyPacing);
  const syncPending = useGameSession((s) => s.syncPending);
  const setConnection = useGameSession((s) => s.setConnection);
  const setMySeat = useGameSession((s) => s.setMySeat);

  const {
    data,
    isPending: loading,
    isFetchedAfterMount,
    error: statusError,
  } = useQuery({
    queryKey: queryKeys.games.status(gameId),
    queryFn: () => getGameStatus(gameId),
    enabled,
    // The page reads its catch-up boundary (`last_seq`) and the server's clock from the first
    // status it holds, so that must be this visit's: a status kept from a visit a few seconds
    // ago (the cache keeps it 30 s) made everything since then play as news, at reading pace,
    // with no "You're back" (2026-10-15). Always asked again, and not used until it answers.
    refetchOnMount: 'always',
    // A waiting room has no stream, so this poll is how joiners see the roster fill and
    // the host press start: keep it quick. Once running the stream carries the game and
    // the poll is only the dead-game detector and the deadline refresh, so it can relax.
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      if (state === 'waiting') return 3_000;
      return state === 'running' ? 12_000 : false;
    },
  });

  const status = isFetchedAfterMount ? data : undefined;
  const isPending = loading || (!isFetchedAfterMount && !statusError);

  // `you` arrives with the status, often after events have already folded.
  useEffect(() => {
    if (!status) return;
    const seat = status.you ?? null;
    recordServerClock(status.server_time);
    setMySeat(seat);
    // InputRequest owns the form shape; status owns whether that request is still current.
    // This clears historical requests after catch-up and refreshes the live deadline.
    syncPending(
      seat,
      status.pending_seats ?? [],
      status.deadlines ?? {},
      status.last_seq ?? 0,
    );
  }, [status, setMySeat, syncPending]);

  useEffect(() => {
    // No stream for a waiting room (nothing to stream yet) or an archived game (the live
    // object is gone; the row answered the poll and the page shows the ended card).
    if (!enabled || !status || status.state === 'waiting' || status.archived) return;
    if (status.awaiting_key) return; // idle until a seat holder funds it; the poll will say

    // Frozen at connect time; every seq at or below it is history, not news (until a reconnect).
    const boundary = catchUpBoundary(status.last_seq ?? 0);
    const history = catchUpBatch(applyCatchUp);
    hydrate([], { gameId, mySeat: status.you ?? null });
    setConnection('connecting');

    // last_seq=0: we want the whole log, and the catch-up boundary above — not a cursor —
    // is what keeps the replay silent. The browser's auto-reconnect reuses this URL
    // verbatim and carries its real position in Last-Event-ID, which the server prefers.
    // A reopen of our own (below) carries the page's position in the URL instead.
    const url = apiUrl(`/games/${encodeURIComponent(gameId)}/events`);
    const connect = (at: string): EventSource => {
      const source = new EventSource(at, { withCredentials: true });
      source.addEventListener('open', () => {
        setConnection('open');
        // back after a drop: ask how far the log has got; up to there is catch-up, not news
        if (boundary.resuming())
          getGameStatus(gameId).then(
            (fresh) => boundary.resumed(fresh.last_seq ?? 0),
            () => boundary.resumed(useGameSession.getState().view.lastSeq),
          );
      });

      source.addEventListener('game', (message) => {
        try {
          const event = JSON.parse(
            (message as MessageEvent<string>).data,
          ) as DurableGameEvent;
          if (boundary.isHistory(event.seq)) history.add(event);
          else {
            history.flush();
            applyLive(event);
          }
        } catch {
          // A frame we cannot parse is a wire problem, not a render problem. Dropping it
          // keeps the session alive; the status poll remains the authority on game state.
        }
      });

      source.addEventListener('pacing', (message) => {
        try {
          applyPacing(JSON.parse((message as MessageEvent<string>).data) as PhaseProgress);
        } catch {
          /* pacing is decorative — never worth breaking a session over */
        }
      });

      source.addEventListener('error', () => {
        // the browser is reopening the stream: what it resends until the fresh status is catch-up
        if (source.readyState === EventSource.CONNECTING) boundary.dropped();
        // A backgrounded tab gets throttled and drops the connection; that is the browser
        // doing its job, not a fault, and surfacing it would cry wolf on every tab switch.
        if (typeof document !== 'undefined' && document.hidden) return;
        setConnection(
          source.readyState === EventSource.CONNECTING ? 'reconnecting' : 'closed',
        );
      });
      return source;
    };
    let source = connect(url);

    // Back from a sleep or a dropped network: reopen now, from the newest seq folded, rather
    // than wait for the browser's retry. Until a fresh status says how far the log has got,
    // what the new stream sends is catch-up, as after any drop. An open stream is left be.
    const reopen = () => {
      if (!reopenNow(source.readyState, document.hidden)) return;
      source.close();
      history.flush();
      boundary.dropped();
      setConnection('reconnecting');
      const at = useGameSession.getState().view.lastSeq;
      source = connect(at > 0 ? `${url}?last_seq=${at}` : url);
    };
    document.addEventListener('visibilitychange', reopen);
    window.addEventListener('online', reopen);

    return () => {
      document.removeEventListener('visibilitychange', reopen);
      window.removeEventListener('online', reopen);
      source.close();
      history.drop();
      setConnection('idle');
    };
    // Reconnect when seat identity changes. Rejoin sets a NEW cookie, but an EventSource's
    // request credential is frozen at open time; keeping the anonymous source would leave a
    // recovered player on the spectator tier. Primitive dependencies avoid reconnecting on
    // every twelve-second status object refresh.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameId, enabled, Boolean(status && status.state !== 'waiting'), status?.you]);

  return {
    status,
    state: status?.state as GameState | undefined,
    error: status?.error ?? null,
    statusError,
    isPending,
  };
}
