'use client';

/**
 * The puppets a player may pick (`GET /characters`), retired ones left out. The catalogue only
 * changes with a deploy, so it is fetched once per visit; while it loads, or if it fails, the
 * list is empty and the screens simply offer no pick (the house draws).
 */
import { useQuery } from '@tanstack/react-query';
import { listCharacters } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import type { CharacterCard } from '@/types/contracts';

const NONE: CharacterCard[] = [];

export function useCharacters(): CharacterCard[] {
  const { data } = useQuery({
    queryKey: queryKeys.characters(),
    queryFn: listCharacters,
    staleTime: Infinity,
    select: (cards) => cards.filter((c) => !c.retired),
  });
  return data ?? NONE;
}
