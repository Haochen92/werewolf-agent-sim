'use client';

import { useQuery } from '@tanstack/react-query';
import { listReplays } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { queryKeys } from '@/lib/queryKeys';
import { ReplayGrid } from '@/components/ReplayCard';
import pageClasses from '@/app/page.module.css';

/**
 * The replay browser. `limit` exists so the landing page can reuse this exact component for
 * its rail of latest replays (D1) rather than growing a second, drifting copy.
 */
export function ReplayListClient({ limit }: { limit?: number }) {
  const { data, isPending, error } = useQuery({
    queryKey: queryKeys.replays.list({ limit }),
    queryFn: () => listReplays(limit === undefined ? {} : { limit }),
  });

  if (isPending) {
    return (
      <div className={pageClasses.doors}>
        <div className={pageClasses.skeletonCard} />
        <div className={pageClasses.skeletonCard} />
        <div className={pageClasses.skeletonCard} />
      </div>
    );
  }

  if (error) {
    // 503 is specifically "the archive isn't configured", which is an operator problem and
    // deserves its own words rather than a generic failure (ux_baseline §3).
    const unavailable = error instanceof ApiError && error.isUnavailable;
    return (
      <p role="alert" className={pageClasses.note}>
        {unavailable
          ? 'The replay archive is not configured on this server.'
          : `Could not load replays: ${error.message}`}
      </p>
    );
  }

  if (data.length === 0) {
    return <p className={pageClasses.note}>No games have been archived yet.</p>;
  }

  return <ReplayGrid replays={data} />;
}
