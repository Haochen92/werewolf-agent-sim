'use client';

/**
 * " · 212 games archived" in the footer's credit line: the archive's total, which
 * `GET /replays` sends in its `X-Total-Count` header. Asked for with a one-row page, and said
 * only once the server has answered; until then (or if it cannot), the phrase is left out
 * rather than guessed.
 */
import { useQuery } from '@tanstack/react-query';
import { listReplaysWithTotal } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';

export function GamesArchived() {
  const { data } = useQuery({
    queryKey: queryKeys.replays.total(),
    queryFn: () => listReplaysWithTotal({ limit: 1 }),
    staleTime: 60_000,
    retry: false,
  });
  if (!data) return null;
  return <> · {data.total === 1 ? '1 game archived' : `${data.total} games archived`}</>;
}
