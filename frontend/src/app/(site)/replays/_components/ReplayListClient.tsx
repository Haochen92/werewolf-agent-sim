'use client';

import { useQuery } from '@tanstack/react-query';
import { listReplays } from '@/lib/api';
import { ApiError } from '@/lib/request';
import { queryKeys } from '@/lib/queryKeys';
import { Slate, SlateGrid } from '@/components/site';
import { useModelLabels } from '@/hooks/useModelLabels';
import { usePlayedHere } from '@/hooks/usePlayedHere';
import pageClasses from '@/app/(site)/page.module.css';

/**
 * The landing's rail of latest games (D1), as slates. The archive itself (`/replays`) is
 * `ArchiveClient`; this stays the small, unfiltered cut for the landing until its own rebuild.
 */
export function ReplayListClient({ limit }: { limit?: number }) {
  const modelName = useModelLabels();
  const mine = usePlayedHere();
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

  return (
    <SlateGrid>
      {data.map((r) => (
        <Slate
          key={r.game_id}
          replay={r}
          modelLabel={r.model ? modelName(r.model) : undefined}
          mine={mine.has(r.game_id)}
        />
      ))}
    </SlateGrid>
  );
}
