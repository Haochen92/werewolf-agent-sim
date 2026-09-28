'use client';

/**
 * The landing's two doors, hung from a rail (the mockup's `.seat-rail`): play solo, or join the
 * others at the departures hall, which is also where a table is opened. The party tag says how
 * many tables are boarding right now, from `GET /rooms` (a room that is neither locked nor
 * full); until the server answers, or if it cannot, it says nothing rather than a number it
 * would have to guess.
 *
 * `stubs` is the same two doors as ticket stubs, the torn-off end of each tag: the "Take a seat"
 * reminder after the roles, a third the size, so it reads as the page's close rather than a
 * second copy of the hero.
 */
import Link from 'next/link';
import { useQuery } from '@tanstack/react-query';
import { HangTag } from '@/components/site';
import { listRooms } from '@/lib/api';
import { queryKeys } from '@/lib/queryKeys';
import { rowFace } from '../../rooms/_components/boarding';
import classes from './Landing.module.css';

function boardingLine(n: number): string {
  if (n === 0) return 'none boarding';
  return n === 1 ? '1 table boarding' : `${n} tables boarding`;
}

export function SeatTags({ stubs = false }: { stubs?: boolean }) {
  const rooms = useQuery({
    queryKey: queryKeys.rooms.list(),
    queryFn: listRooms,
    staleTime: 30_000,
    retry: false,
  });
  const boarding = rooms.data?.filter((r) => rowFace(r).joinable).length;

  if (stubs)
    return (
      <nav className={classes.stubs} aria-label="Take a seat">
        <Link href="/play" className={classes.stub}>
          <span className={classes.stubKicker}>Admit one</span>
          <span className={classes.stubTitle}>Play solo</span>
          <span className={classes.stubGo} aria-hidden="true">
            &rarr;
          </span>
        </Link>
        <Link href="/rooms" className={classes.stub}>
          <span className={classes.stubKicker}>Admit a party</span>
          <span className={classes.stubTitle}>Play with others</span>
          <span className={classes.stubGo}>
            {boarding === undefined ? null : <small>{boardingLine(boarding)}</small>}
            <span aria-hidden="true">&rarr;</span>
          </span>
        </Link>
      </nav>
    );

  return (
    <div className={classes.seatRail}>
      <span className={classes.rail} aria-hidden="true" />
      <HangTag
        href="/play"
        kicker="Admit one"
        title="Play solo"
        foot={['Start a game', '→']}
      >
        One seat at a table of eight agents.
      </HangTag>
      <HangTag
        href="/rooms"
        kicker="Admit a party"
        title="Play with others"
        foot={['Browse tables', boarding === undefined ? '→' : boardingLine(boarding)]}
      >
        Board a table with friends, or open your own and send the link.
      </HangTag>
    </div>
  );
}
