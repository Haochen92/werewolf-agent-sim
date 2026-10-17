'use client';

/**
 * The replay page: fetches the finished game's whole log once and hands it to the replay
 * theatre, which plays it on the stage beat by beat (src/stage/containers/ReplayTheatre).
 * The page itself only waits for the log and says so if it cannot have it.
 *
 * The way in is the house's loading picture over the page (`ReplayCover`, held by the route's
 * layout from the click; owner, 2026-10-16, in place of the train's departure, now the live
 * games' only). The theatre is mounted under it as soon as the log comes (out of sight and
 * inert), so its code has run and its pictures are in before it is seen; the cover lifts off it
 * then, and the theatre starts as it does. What the page cannot have is said at once, and the
 * cover goes. With `?still=1` (the tests and goldens) there is no cover: the same loading
 * picture, drawn by the page while the log is on its way, then the theatre at once.
 *
 * A game is filed as a replay when its run ends, which with memory on is after the lessons are
 * written, a minute or more after `game_over`: a viewer who comes from the live curtain can be
 * early. So a 404 asks the game's status before saying anything (2026-10-01): a game that is
 * over but not yet filed keeps the cover up, "Winding the reels…", and the log is asked for again every few seconds until it comes; a status from the
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
import { Anchor } from '@mantine/core';
import { useSearchParams } from 'next/navigation';
import { useEffect, useRef, useState, type CSSProperties } from 'react';
import { useQuery } from '@tanstack/react-query';
import { TrainLoader } from '@/components/TrainLoader';
import { FILED_POLL_MS } from '@/hooks/useReplayFiled';
import { getGameStatus, getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { picturesOf } from '@/stage/pictures-of';
import { ReplayTheatre } from '@/stage/containers/ReplayTheatre';
import type { GameStatus } from '@/types/contracts';
import { useCover } from './ReplayCover';
import classes from './TheaterClient.module.css';

const HOME = { href: '/', label: 'Home' };

/** The theatre under the platform: laid out, so it measures and fetches, but never painted. */
const UNDER: CSSProperties = { visibility: 'hidden' };

/** How long the curtain waits on the theatre's pictures before it lifts without them. */
const PICTURES_CAP_MS = 4000;

/**
 * What the wait is while a finished game's replay is being filed (on the cover, or on the page's
 * own loader with `?still=1`): a matter of moments, and the page asks again every five seconds
 * and plays it when it comes.
 */
const WINDING = 'Winding the reels…';

/** Over, still live (not yet from its row), its run not dead: the replay is on its way. */
function windingOn(s: GameStatus | undefined): boolean {
  return !!s && !s.archived && s.game_over && !s.error;
}

export function TheaterClient({ gameId }: { gameId: string }) {
  const params = useSearchParams();
  const fromHome = params.get('from') === 'home';
  const still = params.get('still') === '1';
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
  const waiting = isPending || statusPending || retrying || (missing && winding);

  // the log is here: the theatre is drawn under the cover, and once its pictures are in, the
  // cover lifts off it (after its least hold) and the theatre starts
  const cover = useCover();
  const theatre = useRef<HTMLElement>(null);
  const [ready, setReady] = useState(false);
  useEffect(() => {
    if (!data || !theatre.current) return;
    let live = true;
    void picturesOf(theatre.current, PICTURES_CAP_MS).then(() => {
      if (live) setReady(true);
    });
    return () => {
      live = false;
    };
  }, [data]);
  const lifting = cover ? cover.lifting : ready;
  const cue = cover?.cue;
  const winds = missing && winding;
  const off = !data && !waiting;
  useEffect(
    () => cue?.({ line: winds ? WINDING : null, ready, off }),
    [cue, winds, ready, off],
  );

  if (still && waiting)
    return (
      <div className={classes.wait} data-loading="replay">
        <TrainLoader atOnce line={winds ? WINDING : null} />
      </div>
    );
  if (still && data)
    return (
      <OrientationGuard>
        <main className={classes.page}>
          <ReplayTheatre game={data} back={fromHome ? HOME : undefined} />
        </main>
      </OrientationGuard>
    );
  // the layout has the cover over it, and the phone's turn card (`ReplayCover`)
  if (data)
    return (
      <main
        ref={theatre}
        className={classes.page}
        style={lifting ? undefined : UNDER}
        inert={!lifting}
        aria-hidden={lifting ? undefined : true}
      >
        <ReplayTheatre game={data} back={fromHome ? HOME : undefined} waiting={!lifting} />
      </main>
    );
  if (waiting) return null;
  if (missing && (status.data?.state === 'dropped' || live?.error))
    return (
      <p role="alert" className={classes.meta}>
        This game was dropped.{' '}
        <Anchor component={Link} href="/rooms">
          Back to the lobby
        </Anchor>
      </p>
    );
  if (missing && live)
    return (
      <p role="alert" className={classes.meta}>
        This game is still being played.{' '}
        <Anchor component={Link} href={`/games/${encodeURIComponent(gameId)}`}>
          Watch it live
        </Anchor>
      </p>
    );
  if (error && !data) {
    return (
      <p role="alert" className={classes.meta}>
        {missing ? 'No such replay.' : `Could not load this replay: ${error.message}`}{' '}
        <Anchor component={Link} href="/replays">
          Back to the replays
        </Anchor>
      </p>
    );
  }
  return null;
}
