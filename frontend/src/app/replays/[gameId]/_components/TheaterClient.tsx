'use client';

/**
 * The replay page: fetches the finished game's whole log once and hands it to the replay
 * theatre, which plays it on the stage beat by beat (src/stage/containers/ReplayTheatre).
 * The page itself only waits for the log (on the empty platform, `StationStill`) and says so
 * if it cannot have it.
 *
 * A game is filed as a replay when its run ends, which with memory on is after the lessons are
 * written, a minute or more after `game_over`: a viewer who comes from the live curtain can be
 * early. So a 404 asks the game's status before saying anything (2026-10-01): a game that is
 * over but not yet filed keeps the platform up, "Winding the reels… come back in a few
 * minutes", and the log is asked for again every few seconds until it comes; a status from the
 * game's row (archived) means the replay landed between the two calls, and the log is asked
 * for once more at once; a dropped game says so; only an id the server does not know at all
 * is "No such replay."
 *
 * Nothing here gates on entitlement. The archive serves every tier for a finished game, so
 * the X-ray is an arrangement of what is shown, never a question of what the viewer may know.
 *
 * The page is landscape only (stage_architecture.md, ruling 3): upright, a card asks the
 * viewer to turn the phone.
 *
 * The theatre's way out goes back where the viewer came from: the landing's links say so with
 * `?from=home`; anything else (the archive, a live game's end, a shared link) goes to the list.
 */
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { FILED_POLL_MS } from '@/hooks/useReplayFiled';
import { getGameStatus, getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { ReplayTheatre } from '@/stage/containers/ReplayTheatre';
import { StationStill } from '@/stage/scenes/StationStill';
import type { GameStatus } from '@/types/contracts';
import classes from './TheaterClient.module.css';

const HOME = { href: '/', label: 'Home' };

/** The still's line while a finished game's replay is being filed (the curtain's plaque's). */
const WINDING = 'Winding the reels… come back in a few minutes';

/** Over, still live (not yet from its row), its run not dead: the replay is on its way. */
function windingOn(s: GameStatus | undefined): boolean {
  return !!s && !s.archived && s.game_over && !s.error;
}

export function TheaterClient({ gameId }: { gameId: string }) {
  const fromHome = useSearchParams().get('from') === 'home';
  // the game's status, asked only when the replay is not there (see `winding`, below)
  const [asked, setAsked] = useState(false);
  const status = useQuery({
    queryKey: queryKeys.games.status(gameId),
    queryFn: () => getGameStatus(gameId),
    enabled: asked,
    retry: false,
    // while it winds, the status is asked too: a run that dies in its last step is dropped
    refetchInterval: (query) => (windingOn(query.state.data) ? FILED_POLL_MS : false),
  });
  const live = status.data && !status.data.archived ? status.data : undefined;
  const winding = windingOn(status.data);
  const { data, isPending, isFetching, error, refetch } = useQuery({
    queryKey: queryKeys.replays.detail(gameId),
    queryFn: () => getReplay(gameId),
    staleTime: Infinity, // a finished replay is immutable
    refetchInterval: (query) => (winding && !query.state.data ? FILED_POLL_MS : false),
  });
  const missing = !data && error instanceof ApiError && error.status === 404;
  useEffect(() => {
    if (missing) setAsked(true);
  }, [missing]);
  // the status came from the game's row: the replay landed between the two calls, ask once more
  const [retried, setRetried] = useState(false);
  const filedSince =
    missing && status.data?.archived && status.data.state === 'finished' && !retried;
  useEffect(() => {
    if (!filedSince) return;
    setRetried(true);
    void refetch();
  }, [filedSince, refetch]);

  const statusPending = missing && (!asked || status.isPending);
  const retrying = filedSince || (missing && retried && isFetching);
  if (isPending || statusPending || retrying)
    return <StationStill what="replay" hud="replay" line="Rewinding the reels…" />;
  if (missing && winding) return <StationStill what="replay" hud="replay" line={WINDING} />;
  if (missing && (status.data?.state === 'dropped' || live?.error))
    return (
      <p role="alert" className={classes.meta}>
        This game was dropped. <Link href="/rooms">Back to the lobby</Link>
      </p>
    );
  if (missing && live)
    return (
      <p role="alert" className={classes.meta}>
        This game is still being played.{' '}
        <Link href={`/games/${encodeURIComponent(gameId)}`}>Watch it live</Link>
      </p>
    );
  if (error && !data) {
    return (
      <p role="alert" className={classes.meta}>
        {missing ? 'No such replay.' : `Could not load this replay: ${error.message}`}{' '}
        <Link href="/replays">Back to the replays</Link>
      </p>
    );
  }
  if (!data) return null;

  return (
    <OrientationGuard>
      <main className={classes.page}>
        <ReplayTheatre game={data} back={fromHome ? HOME : undefined} />
      </main>
    </OrientationGuard>
  );
}
