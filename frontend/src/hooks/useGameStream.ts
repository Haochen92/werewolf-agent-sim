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
 * snapshot's `last_seq` is folded as HISTORY; only what is above it counts as news and can
 * fire a beat. Without that split, every refresh would replay the role reveal and the
 * game-over takeover for events that happened an hour ago (ux_journeys §0, D23).
 */
import { useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { apiUrl } from '@/lib/config';
import { getGameStatus } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { useGameSession } from '@/game/store';
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
  isPending: boolean;
}

export function useGameStream(gameId: string, enabled = true): GameStream {
  const hydrate = useGameSession((s) => s.hydrate);
  const applyLive = useGameSession((s) => s.applyLive);
  const applyCatchUp = useGameSession((s) => s.applyCatchUp);
  const applyPacing = useGameSession((s) => s.applyPacing);
  const setConnection = useGameSession((s) => s.setConnection);
  const setMySeat = useGameSession((s) => s.setMySeat);

  // Frozen at connect time; every seq at or below it is history, not news.
  const catchUpThrough = useRef<number>(0);
  const opened = useRef(false);

  const { data: status, isPending } = useQuery({
    queryKey: queryKeys.games.status(gameId),
    queryFn: () => getGameStatus(gameId),
    enabled,
    // Keep polling while the game runs: this is the dead-game detector, and it also
    // refreshes pending_seats / deadlines for the lobby-ish parts of the UI.
    refetchInterval: (query) => {
      const state = query.state.data?.state;
      return state === 'running' || state === 'waiting' ? 12_000 : false;
    },
  });

  // `you` arrives with the status, often after events have already folded.
  useEffect(() => {
    if (status?.you !== undefined) setMySeat(status.you ?? null);
  }, [status?.you, setMySeat]);

  useEffect(() => {
    if (!enabled || !status || opened.current) return;
    opened.current = true;

    catchUpThrough.current = status.last_seq ?? 0;
    hydrate([], { gameId, mySeat: status.you ?? null });
    setConnection('connecting');

    // last_seq=0: we want the whole log, and the catch-up boundary above — not a cursor —
    // is what keeps the replay silent. The browser's auto-reconnect reuses this URL
    // verbatim and carries its real position in Last-Event-ID, which the server prefers.
    const source = new EventSource(apiUrl(`/games/${encodeURIComponent(gameId)}/events`), {
      withCredentials: true,
    });

    source.addEventListener('open', () => setConnection('open'));

    source.addEventListener('game', (message) => {
      try {
        const event = JSON.parse(
          (message as MessageEvent<string>).data,
        ) as DurableGameEvent;
        if (event.seq <= catchUpThrough.current) applyCatchUp(event);
        else applyLive(event);
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
      // A backgrounded tab gets throttled and drops the connection; that is the browser
      // doing its job, not a fault, and surfacing it would cry wolf on every tab switch.
      if (typeof document !== 'undefined' && document.hidden) return;
      setConnection(
        source.readyState === EventSource.CONNECTING ? 'reconnecting' : 'closed',
      );
    });

    return () => {
      source.close();
      opened.current = false;
      setConnection('idle');
    };
    // Deliberately keyed on gameId alone: re-running this on every status refetch would
    // tear down and rebuild the stream every twelve seconds.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [gameId, enabled, Boolean(status)]);

  return {
    status,
    state: status?.state as GameState | undefined,
    error: status?.error ?? null,
    isPending,
  };
}
