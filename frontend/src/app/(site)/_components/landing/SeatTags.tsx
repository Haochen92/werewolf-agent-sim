'use client';

/**
 * The landing's two doors (owner, 2026-10-18: flat paper tickets on the night scene, HeroTicket):
 * play solo, or join the others at the departures hall, which is also where a table is opened.
 * The party ticket says how many tables are boarding right now, from `GET /rooms` (a room that
 * is neither locked nor full); until the server answers, or if it cannot, it says nothing rather
 * than a number it would have to guess. On a phone each ticket is its title and the way in, the
 * count under the party's title only while a table is boarding.
 */
import { useBoarding } from '@/hooks/useBoarding';
import { HeroTicket } from './HeroTicket';
import classes from './Landing.module.css';

function boardingLine(n: number): string {
  if (n === 0) return 'none boarding';
  return n === 1 ? '1 table boarding' : `${n} tables boarding`;
}

export function SeatTags() {
  const boarding = useBoarding();

  return (
    <div className={classes.tickets}>
      <HeroTicket href="/play" kicker="Admit one" title="Play solo">
        One seat at a table of agents.
      </HeroTicket>
      <HeroTicket
        href="/rooms"
        kicker="Admit a party"
        title="Play with others"
        foot={boarding === undefined ? undefined : boardingLine(boarding)}
        note={boarding ? boardingLine(boarding) : undefined}
      >
        Board a table with friends, or open your own and send the link.
      </HeroTicket>
    </div>
  );
}
