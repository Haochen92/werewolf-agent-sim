'use client';
/**
 * The models' display names from `GET /models` (review §B9: the server's spelling wins), as a
 * lookup from id to label. An id the menu no longer lists (a retired model) reads as itself, and
 * so does every id while the menu loads or if it fails, so a slate never waits on it.
 */
import { useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';
import { getModels } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';

export function useModelLabels(): (id: string) => string {
  const { data } = useQuery({ queryKey: queryKeys.models(), queryFn: getModels });
  const labels = useMemo(
    () => new Map((data?.models ?? []).map((row) => [row.model, row.label])),
    [data],
  );
  return useCallback((id: string) => labels.get(id) ?? id, [labels]);
}
