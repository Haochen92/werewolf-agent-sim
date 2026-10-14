'use client';

/**
 * The landing's two doors, hung from a rail (the mockup's `.seat-rail`): play solo, or join the
 * others at the departures hall, which is also where a table is opened. The party tag says how
 * many tables are boarding right now, from `GET /rooms` (a room that is neither locked nor
 * full); until the server answers, or if it cannot, it says nothing rather than a number it
 * would have to guess. On a phone each tag is its stub (HangTag), the count under its title.
 */
import { HangTag } from '@/components/site';
import { useBoarding } from '@/hooks/useBoarding';
import classes from './Landing.module.css';

function boardingLine(n: number): string {
  if (n === 0) return 'none boarding';
  return n === 1 ? '1 table boarding' : `${n} tables boarding`;
}

export function SeatTags() {
  const boarding = useBoarding();

  return (
    <div className={classes.seatRail}>
      <span className={classes.rail} aria-hidden="true" />
      <HangTag
        href="/play"
        kicker="Admit one"
        title="Play solo"
        foot={['Start a game', '→']}
      >
        One seat at a table of agents.
      </HangTag>
      <HangTag
        href="/rooms"
        kicker="Admit a party"
        title="Play with others"
        foot={['Browse tables', boarding === undefined ? '→' : boardingLine(boarding)]}
        note={boarding === undefined ? undefined : boardingLine(boarding)}
      >
        Board a table with friends, or open your own and send the link.
      </HangTag>
    </div>
  );
}
