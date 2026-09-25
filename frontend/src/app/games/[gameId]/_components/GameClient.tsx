'use client';

/**
 * `/games/[gameId]` — ONE route, three states (build_plan §5).
 *
 *   waiting  → the lobby card
 *   running  → the live theatre: the SAME stage and scenes the replay uses, fed by the SSE
 *              store instead of a fetched log, with the seated human's turns on it
 *   finished → the same theatre, played on to its curtain with the X-ray on for everyone
 *
 * The client never re-routes across those transitions; the page morphs, mirroring the
 * server's own registry swap where a room URL becomes a game URL.
 *
 * Beats fire on LIVE arrival only: the theatre plays what arrives while the page watches and
 * lands still on whatever the log already held, so a refresh mid-game lands silently on the
 * latest beat instead of replaying an hour of drama (ux_journeys §0, D23).
 *
 * The room is landscape only (stage_architecture.md, ruling 3): upright, a card asks the
 * viewer to turn the phone. The waiting lobby stays an ordinary responsive page.
 */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { useGameStream } from '@/hooks/useGameStream';
import { queryKeys } from '@/lib/queryKeys';
import { rejoinGame } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { hostKey, seatToken } from '@/lib/storage';
import { LobbyCard, TerminalError } from '@/components/LobbyCard';
import { GameEndedCard } from '@/components/GameEndedCard';
import { KeyNeededCard } from '@/components/KeyNeededCard';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { LiveTheatre } from '@/stage/containers/LiveTheatre';
import classes from './GameClient.module.css';

export function GameClient({ gameId }: { gameId: string }) {
  const queryClient = useQueryClient();
  const { status, state, error, statusError, isPending } = useGameStream(gameId);

  /**
   * Seat recovery (D23). The trigger is NOT a failed request: a lost cookie does not make
   * `GET /games/{id}` fail — it succeeds and simply reports `you: null`, because that call
   * is public. So the real signal is "this device holds a seat token for this game, yet the
   * server says we are nobody", which means the HttpOnly cookie is gone (cleared data, new
   * browser session) while its localStorage backup survived. One attempt, then we stay a
   * spectator: cross-device rejoin is deliberately v1-out.
   */
  const [rejoinTried, setRejoinTried] = useState(false);
  const [rejoining, setRejoining] = useState(false);
  useEffect(() => {
    setRejoinTried(false);
    setRejoining(false);
  }, [gameId]);

  useEffect(() => {
    const seatMissing = Boolean(status && !status.you);
    const seatRejected = statusError instanceof ApiError && statusError.isSeatLost;
    if (rejoinTried || (!seatMissing && !seatRejected)) return;
    const token = seatToken.get(gameId);
    if (!token) return;
    setRejoinTried(true);
    setRejoining(true);
    rejoinGame(gameId, token)
      .then(() =>
        queryClient.invalidateQueries({ queryKey: queryKeys.games.status(gameId) }),
      )
      .catch(() => {
        // The token no longer resolves (game gone, or a different device's seat).
        seatToken.clear(gameId);
      })
      .finally(() => setRejoining(false));
  }, [gameId, status, statusError, rejoinTried, queryClient]);

  if (isPending || rejoining) {
    return (
      <p className={classes.meta}>{rejoining ? 'Reclaiming your seat…' : 'Joining…'}</p>
    );
  }

  if (statusError) {
    const missing = statusError instanceof ApiError && statusError.status === 404;
    // Rooms live only in the server's memory, so a restart closes them. If this browser
    // holds a host key or seat for the id, that is what happened; say so rather than
    // "unknown".
    const wasOurRoom = missing && Boolean(hostKey.get(gameId) || seatToken.get(gameId));
    return (
      <div className={classes.shell}>
        <p role="alert" className={classes.meta}>
          {wasOurRoom
            ? 'This room closed when the server restarted. Rooms are not saved; open a new one.'
            : missing
              ? 'No game has this id.'
              : statusError.message}
        </p>
        <p className={classes.meta}>
          <Link href="/">Back to the start →</Link>
        </p>
      </div>
    );
  }

  // The game ended and left the live registry: the poll answered from the row and there
  // is no stream. Finished games link to their replay; dropped ones say why.
  if (status?.archived) return <GameEndedCard gameId={gameId} status={status} />;

  // Live but idle: it ran on a player's key that a restart forgot. A seat holder can
  // enter it again; everyone else sees why the game is paused.
  if (status?.awaiting_key) return <KeyNeededCard gameId={gameId} status={status} />;

  // D23: the game task died. The stream cannot tell us this — only the poll's error field
  // can, because heartbeats keep flowing and `state` stays "running".
  if (error) return <TerminalError message={error} byok={status?.name?.includes('byok')} />;

  if (state === 'waiting' && status) return <LobbyCard gameId={gameId} status={status} />;

  return (
    <OrientationGuard>
      <main className={classes.page}>
        <LiveTheatre gameId={gameId} status={status} />
      </main>
    </OrientationGuard>
  );
}
