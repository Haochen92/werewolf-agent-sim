/**
 * The landing's two doors (owner, 2026-10-18: flat paper tickets on the night scene, HeroTicket):
 * play solo, or join the others at the departures hall, which is also where a table is opened.
 * How many tables are boarding is the nav's Rooms door's to say (owner, 2026-10-18: one counter).
 */
import { HeroTicket } from './HeroTicket';
import classes from './Landing.module.css';

export function SeatTags() {
  return (
    <div className={classes.tickets}>
      <HeroTicket href="/play" kicker="Admit one" title="Play solo">
        One seat at a table of agents.
      </HeroTicket>
      <HeroTicket href="/rooms" kicker="Admit a party" title="Play with others">
        Board a table with friends, or open your own and send the link.
      </HeroTicket>
    </div>
  );
}
