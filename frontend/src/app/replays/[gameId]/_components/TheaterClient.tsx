'use client';

/**
 * The replay page: fetches the finished game's whole log once and hands it to the replay
 * theatre, which plays it on the stage beat by beat (src/stage/containers/ReplayTheatre).
 * The page itself only waits for the log and says so if it cannot have it.
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
import { useQuery } from '@tanstack/react-query';
import { getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { ApiError } from '@/lib/request';
import { OrientationGuard } from '@/stage/OrientationGuard';
import { ReplayTheatre } from '@/stage/containers/ReplayTheatre';
import classes from './TheaterClient.module.css';

const HOME = { href: '/', label: 'Home' };

export function TheaterClient({ gameId }: { gameId: string }) {
  const fromHome = useSearchParams().get('from') === 'home';
  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.replays.detail(gameId),
    queryFn: () => getReplay(gameId),
    staleTime: Infinity, // a finished replay is immutable
  });

  if (isPending) return <p className={classes.meta}>Loading replay…</p>;
  if (error) {
    const missing = error instanceof ApiError && error.status === 404;
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
