'use client';

/**
 * Whether a finished game's replay is filed yet. The replay is filed when the engine's run
 * ends, which with memory on is after the lessons are written, a minute or more after
 * `game_over`; until then `GET /replays/{id}` is a 404. The status cannot say it while a page
 * watches: a game leaves the live registry (and its status turns `archived`) only once nobody
 * is watching it. So, while `waiting`, ask the archive every few seconds until it answers. The
 * answer is the replay itself, kept under the replay page's own key, so "Watch the replay"
 * opens on it at once.
 */
import { useQuery } from '@tanstack/react-query';
import { getReplay } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';

/** How often to ask while the replay is not filed (the replay page's wait asks as often). */
export const FILED_POLL_MS = 5_000;

export function useReplayFiled(gameId: string, waiting: boolean): boolean {
  const { data } = useQuery({
    queryKey: queryKeys.replays.detail(gameId),
    queryFn: () => getReplay(gameId),
    enabled: waiting,
    staleTime: Infinity, // a filed replay is immutable
    retry: false, // a 404 is the answer "not yet"; the interval asks again
    refetchInterval: (query) => (query.state.data ? false : FILED_POLL_MS),
  });
  return data !== undefined;
}
