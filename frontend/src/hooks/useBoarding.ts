'use client';
/**
 * How many tables are boarding right now (a room that is neither locked nor full, `rowFace`),
 * from `GET /rooms`; undefined until the server has answered, or if it cannot. The nav's Rooms
 * counter and the landing's party tag read it, and share one request with the departures board
 * (same query key), which also keeps it fresh while that page polls.
 */
import { useQuery } from '@tanstack/react-query';
import { rowFace } from '@/app/(site)/rooms/_components/boarding';
import { listRooms } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';

export function useBoarding(): number | undefined {
  const rooms = useQuery({
    queryKey: queryKeys.rooms.list(),
    queryFn: listRooms,
    staleTime: 30_000,
    retry: false,
  });
  // the nav is on every page: an answer that is not a list says nothing, never breaks the page
  if (!Array.isArray(rooms.data)) return undefined;
  return rooms.data.filter((r) => rowFace(r).joinable).length;
}
