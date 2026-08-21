'use client';

import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { listReplays } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { queryKeys } from '@/lib/queryKeys';

/**
 * Walking-skeleton replay browser: a plain list, no cards, no pagination chrome. Its only
 * job is proving that a real archive row reaches the browser (P0's done-when). D2's
 * responsive card component replaces the markup in the presentational pass.
 */
export function ReplayListClient() {
  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.replays.list(),
    queryFn: () => listReplays(),
  });

  if (isPending) return <p>Loading replays…</p>;

  if (error) {
    // 503 is the archive-not-configured case and deserves its own words (ux_baseline §3).
    const unavailable = error instanceof ApiError && error.isUnavailable;
    return (
      <p role="alert">
        {unavailable
          ? 'The replay archive is not configured on this server.'
          : `Could not load replays: ${error.message}`}
      </p>
    );
  }

  if (data.length === 0) return <p>No replays archived yet.</p>;

  return (
    <ul>
      {data.map((replay) => (
        <li key={replay.game_id}>
          <Link href={`/replays/${replay.game_id}`}>{replay.game_id}</Link> —{' '}
          {replay.winner} won · {replay.days} days · {replay.n_events} events ·{' '}
          {Object.values(replay.cast_role_counts).reduce((a, b) => a + b, 0)} seats
          {replay.n_humans > 0 ? ` · ${replay.n_humans} human` : ''}
        </li>
      ))}
    </ul>
  );
}
