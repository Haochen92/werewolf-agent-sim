import { HangTag } from '@/components/site';
import { DeparturesBoard } from './_components/DeparturesBoard';
import classes from './_components/Departures.module.css';

export const metadata = { title: 'Rooms' };

/**
 * The lobby: the list of rooms (rooms mockup, review §A3), an ordinary responsive page. The
 * title beside two doors (open a table of your own, or play solo), hung from a hairline as the
 * ticket office's are, then the departures board.
 */
export default function RoomsPage() {
  return (
    <main className={classes.hall}>
      <header className={classes.head}>
        <div>
          <h1 className={classes.title}>The departures hall</h1>
          <p className={classes.lede}>
            Tables waiting for players. Board one, or open your own and send the link.
          </p>
        </div>
        <nav className={classes.doors} aria-label="Other ways aboard">
          <span className={classes.rail} aria-hidden="true" />
          <HangTag href="/rooms/new" kicker="Admit a party" title="Open a table">
            Choose the model, then wait in the room for whoever boards.
          </HangTag>
          <HangTag href="/play" kicker="Admit one" title="Play solo">
            One seat at a table of agents.
          </HangTag>
        </nav>
      </header>

      <DeparturesBoard />
    </main>
  );
}
