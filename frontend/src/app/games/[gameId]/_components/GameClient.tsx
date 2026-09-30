'use client';

/**
 * `/games/[gameId]` — ONE route, three states (build_plan §5).
 *
 *   waiting  → the waiting room: the platform, a scene on the same stage the game plays on
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
 * The room is landscape only (stage_architecture.md, ruling 3; review 2026-09-26 F1): upright, a
 * card asks the viewer to turn the phone. The waiting room is the stage too: the platform
 * (`StationScene`), mounted in the same guard and the same `LiveTheatre` as the game, so when
 * the host departs the train pulls out and the deal begins on the one stage, nothing
 * remounted. The one step allowed upright is the boarding pass (the name a newcomer boards
 * with), a page before the guard; a full or locked room, or "Just watch", skips it. While the
 * status or a rejoin is on its way, the page is the empty platform (`StationStill`).
 */
import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useQueryClient } from '@tanstack/react-query';
import { useGameStream } from '@/hooks/useGameStream';
import { queryKeys } from '@/lib/queryKeys';
import { rejoinGame } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { hostKey, seatToken } from '@/lib/storage';
import { GameEndedCard } from '@/components/GameEndedCard';
import { KeyNeededCard } from '@/components/KeyNeededCard';
import { TerminalError } from '@/components/TerminalError';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { LiveTheatre } from '@/stage/containers/LiveTheatre';
import { StationStill } from '@/stage/scenes/StationStill';
import { BoardingPass } from './BoardingPass';
import classes from './GameClient.module.css';
import { useRoom } from './useRoom';

export function GameClient({ gameId }: { gameId: string }) {
  const queryClient = useQueryClient();
  const { status, state, error, statusError, isPending } = useGameStream(gameId);
  const { room, departed, onRoomAct, boarded } = useRoom(gameId, status);
  // "Just watch" on the boarding pass: the platform without a seat
  const [watching, setWatching] = useState(false);

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
    // A waiting room never names `you` (seats are dealt at the start), so "nobody" is not a
    // lost seat there: the token alone boards you, and rejoining would only blank the platform.
    const seatMissing = Boolean(status && !status.you && status.state !== 'waiting');
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

  // the wait: the empty platform the room or the game takes over (beat sheet §1a)
  if (isPending || rejoining) {
    return (
      <StationStill what="game" line={rejoining ? 'Reclaiming your seat…' : 'Boarding…'} />
    );
  }

  // The room closed before it departed (its host closed it, or nobody departed in time): the
  // server says why, and the way on is another room.
  if (statusError instanceof ApiError && statusError.status === 410) {
    const why = statusError.message;
    return (
      <div className={classes.shell}>
        <p role="alert" className={classes.meta}>
          {why.charAt(0).toUpperCase() + why.slice(1)}.
        </p>
        <p className={classes.meta}>
          <Link href="/rooms">Find another room →</Link>
        </p>
      </div>
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

  // a newcomer to an open room with a place left gives their name first (upright is fine)
  const open = room && !room.locked && room.aboard.length < room.places;
  if (state === 'waiting' && status && room && !room.seated && open && !watching)
    return (
      <BoardingPass
        gameId={gameId}
        status={status}
        onBoarded={boarded}
        onWatch={() => setWatching(true)}
      />
    );

  return (
    <OrientationGuard>
      <main className={classes.page}>
        <LiveTheatre
          gameId={gameId}
          status={status}
          room={room}
          departed={departed}
          onRoomAct={onRoomAct}
        />
      </main>
    </OrientationGuard>
  );
}
