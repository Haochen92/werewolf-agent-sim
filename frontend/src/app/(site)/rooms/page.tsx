import { HangTag } from '@/components/site';
import { DeparturesBoard } from './_components/DeparturesBoard';
import classes from './_components/Departures.module.css';

export const metadata = { title: 'Rooms' };

/**
 * The lobby: the list of rooms (rooms mockup, review §A3), an ordinary responsive page. The
 * departures board, then two doors: open a table of your own, or play solo.
 */
export default function RoomsPage() {
  return (
    <main className={classes.hall}>
      <header className={classes.head}>
        <h1 className={classes.title}>The departures hall</h1>
        <p className={classes.lede}>
          Tables waiting for players. Board one, or open your own and send the link.
        </p>
      </header>

      <DeparturesBoard />

      <nav className={classes.doors} aria-label="Other ways aboard">
        <HangTag
          href="/rooms/new"
          kicker="Admit a party"
          title="Open a table"
          foot={['Open a table', '→']}
        >
          Choose the model and the key, then wait in the room for whoever boards.
        </HangTag>
        <HangTag
          href="/play"
          kicker="Admit one"
          title="Play solo"
          foot={['Start a game', '→']}
        >
          One seat at a table of eight agents.
        </HangTag>
      </nav>
    </main>
  );
}
