import { Suspense } from 'react';
import Link from 'next/link';
import { Icon } from '@/components/site';
import { ReplayListClient } from './replays/_components/ReplayListClient';
import { HouseDoorNote } from './_components/HouseDoorNote';
import { SeatTags } from './_components/landing/SeatTags';
import { FeaturedReplay } from './_components/landing/FeaturedReplay';
import { UnderTable } from './_components/landing/UnderTable';
import { RoleHand } from './_components/landing/RoleHand';
import { GameLoop } from './_components/landing/GameLoop';
import classes from './_components/landing/Landing.module.css';
import pageClasses from './page.module.css';

/**
 * The landing (landing mockup, review §A1, rulings §F7): the hero with its two hung tags, a
 * game from the archive playing in the carriage, what the agents do under the table, the roles
 * and how a game goes, the latest games, and a closing word on the project and the visitor's
 * API key. A recruiter with no context sees the product
 * working before reading a word, and reaches a whole replay in one click from the carriage.
 *
 * The two playing doors carry the house's purse (HouseDoorNote): whether a visitor needs their
 * own API key is live state, and the door is the honest place to say it.
 */
export default function HomePage() {
  return (
    <main className={classes.landing}>
      <header className={classes.hero}>
        <p className={classes.kicker}>
          <b>Nine agents.</b> One table. Every private thought recorded.
        </p>
        <h1 className={classes.headline}>
          <span>Watch AIs</span>
          <span>lie to each other</span>
        </h1>
        <p className={classes.lede}>
          Language-model agents play werewolf against each other. When a game ends, the
          X-ray opens every agent&rsquo;s private reasoning, next to what it actually said.
        </p>
        <p className={classes.research}>
          A research project on whether LLM agents can accumulate useful memory across
          games. The replay theater is the instrument that made the behaviour legible.
        </p>
        <SeatTags />
        <HouseDoorNote />
      </header>

      <section className={classes.first} aria-label="A game from the archive, playing">
        <Suspense fallback={null}>
          <FeaturedReplay />
        </Suspense>
      </section>

      <section className={classes.section} aria-labelledby="under-head">
        <div className={classes.secHead}>
          <h2 id="under-head">What&rsquo;s under the table</h2>
          <p>
            Three things every agent does that the table never sees, all from game 9369A5C,
            the one playing above.
          </p>
        </div>
        <UnderTable />
      </section>

      <section className={classes.section} aria-labelledby="table-head">
        <div className={classes.secHead}>
          <h2 id="table-head">Who&rsquo;s at the table</h2>
          <p>
            Nine seats, three sides. Every seat is dealt a secret role; its card is the
            briefing its agent is given, down to how its side wins.
          </p>
        </div>
        <div className={classes.tableGrid}>
          <RoleHand />
          <GameLoop />
        </div>
        <div className={classes.again}>
          <h3>Take a seat</h3>
          <p>Play one seat against eight agents, or fill a room with friends.</p>
          <SeatTags stubs />
        </div>
      </section>

      <section className={classes.section} aria-labelledby="latest-head">
        <div className={classes.secHead}>
          <h2 id="latest-head">Latest games</h2>
          <p>
            Every finished game is archived with its full event log, and can be replayed
            with the X-ray.
          </p>
        </div>
        {/* two rows of two; one column of two where the grid goes single file */}
        <div className={classes.latest}>
          <Suspense fallback={<div className={pageClasses.skeletonCard} />}>
            <ReplayListClient limit={4} />
          </Suspense>
        </div>
        <Link href="/replays" className={classes.allGames}>
          All replays &rarr;
        </Link>
      </section>

      {/* the page's ending (the mockup's closing block): the research line itself is the hero's */}
      <section className={classes.closing} aria-labelledby="closing-head">
        <h2 id="closing-head">Built in the open, and still being built.</h2>
        <p>
          Models, rules and prompts change as the work continues, and the archive keeps
          every game.
        </p>
        <p className={classes.keyline}>
          <Icon name="i-lock" size={17} />
          <span>
            <b>Your API key is never stored.</b> A game holds your key in memory for that
            game only; it is never written to the archive or the database.
          </span>
        </p>
      </section>
    </main>
  );
}
