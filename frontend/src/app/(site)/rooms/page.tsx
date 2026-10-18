import hallTall from '@/assets/site/hall-tall.webp';
import hallWall from '@/assets/site/hall-wall.webp';
import hallWide from '@/assets/site/hall-wide.webp';
import { PageMusic } from '@/music/PageMusic';
import { HeroTicket } from '../_components/landing/HeroTicket';
import { DeparturesBoard } from './_components/DeparturesBoard';
import classes from './_components/Departures.module.css';

export const metadata = { title: 'Rooms' };

/** A screen wide enough for the column to stand right of the passenger on the bench (repeated
 *  in Departures.module.css, which says why these widths). */
const BESIDE =
  '(min-aspect-ratio: 3/2) and (min-width: 1500px), (min-aspect-ratio: 8/5) and (min-width: 1438px), (min-aspect-ratio: 16/9) and (min-width: 1362px)';

/**
 * The lobby: the list of rooms (owner's mock, 2026-10-18). The night platform's wall, one still
 * picture from the page's top; over it the title beside the landing's two paper tickets (open a
 * table of your own, or play solo), then the departures board. A passenger waits on the bench:
 * beside the board on a screen wide enough, and on a narrower one after it, the page's last
 * picture, so the board never stands over them (owner). Each screen fetches only its own files.
 */
export default function RoomsPage() {
  return (
    <main className={classes.hall}>
      {/* art direction, one file a screen: a plain picture, not next/image */}
      <picture className={classes.scene}>
        <source media="(max-aspect-ratio: 1/1)" srcSet={hallTall.src} />
        <source media={BESIDE} srcSet={hallWide.src} />
        <img src={hallWall.src} alt="" fetchPriority="high" decoding="async" />
      </picture>
      <PageMusic bed="lobby" />
      <div className={classes.column}>
        <header className={classes.head}>
          <div>
            <h1 className={classes.title}>The departures hall</h1>
            <p className={classes.lede}>
              Tables waiting for players. Board one, or open your own and send the link.
            </p>
          </div>
          <nav className={classes.doors} aria-label="Other ways aboard">
            <HeroTicket href="/rooms/new" kicker="Admit a party" title="Open a table">
              Choose the model, then wait in the room for whoever boards.
            </HeroTicket>
            <HeroTicket href="/play" kicker="Admit one" title="Play solo">
              One seat at a table of agents.
            </HeroTicket>
          </nav>
        </header>

        <DeparturesBoard />
      </div>
      {/* the bench after the board on a narrower screen; lazy, so a wide screen never fetches it */}
      <picture className={classes.bench}>
        <source media="(max-aspect-ratio: 1/1)" srcSet={hallTall.src} />
        <img src={hallWide.src} alt="" loading="lazy" decoding="async" />
      </picture>
    </main>
  );
}
