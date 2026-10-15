'use client';

/**
 * The claim ledger the agents read each morning (`GET /games/{id}/ledger`), for the case file's
 * Record. A replay asks once (`morning: 'final'`, the log is finished); a live game asks again
 * when a new morning arrives (the morning is in the key), keeping the last answer on show while
 * the next one comes. If it fails, or until it answers, there is none, and the Record shows the
 * day summaries' own claims, unchecked.
 */
import { keepPreviousData, useQuery } from '@tanstack/react-query';
import { getLedger } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import type { LedgerDay } from '@/types/contracts';

export function useLedger(
  gameId: string,
  morning: number | 'final',
  enabled = true,
): readonly LedgerDay[] | null {
  const { data } = useQuery({
    queryKey: queryKeys.games.ledger(gameId, morning),
    queryFn: () => getLedger(gameId),
    // the first ledger is read on the morning of day 2
    enabled: enabled && (morning === 'final' || morning >= 2),
    staleTime: Infinity, // a morning's ledger never changes
    retry: false,
    placeholderData: keepPreviousData,
  });
  return data ?? null;
}
