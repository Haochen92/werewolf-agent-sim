import { Suspense } from 'react';
import Link from 'next/link';
import { Icon } from '@/components/site';
import { Pendant, WallLight } from '@/components/site/StationLamps';
import { ReplayListClient } from './replays/_components/ReplayListClient';
import { HouseDoorNote } from './_components/HouseDoorNote';
import { SeatTags } from './_components/landing/SeatTags';
import { FeaturedReplay } from './_components/landing/FeaturedReplay';
import { PlatformBackdrop } from './_components/landing/PlatformBackdrop';
import platform from './_components/landing/PlatformBackdrop.module.css';
import { Features } from './_components/landing/Features';
import { RoleHand } from './_components/landing/RoleHand';
import rooms from './_components/landing/Rooms.module.css';
import classes from './_components/landing/Landing.module.css';
import pageClasses from './page.module.css';

/**
 * The landing (landing mockup, review §A1, rulings §F7): the hero with its two hung tags, a
 * game from the archive playing in the carriage, what makes it different, the roles (the rules
 * live on `/guide`), the latest games, and a closing word on the project and the visitor's
 * API key. A recruiter with no context sees the product
 * working before reading a word, and reaches a whole replay in one click from the carriage.
 *
 * Under the carriage each section is a room of the station (Rooms.module.css), one running into
 * the next through the dark: granite under a caged wall light, the roles against a band of green
 * tile, the latest games under a pendant. The way to play is the hero's tags and the nav.
 *
 * The two playing doors carry the house's purse (HouseDoorNote): whether a visitor needs their
 * own API key is live state, and the door is the honest place to say it.
 */
export default function HomePage() {
  return (
    <main className={`${classes.landing} ${platform.scene}`}>
      <PlatformBackdrop />
      <header className={classes.hero}>
        <p className={classes.kicker}>
          <b>Werewolf, played by AI agents.</b> Every private thought recorded.
        </p>
        <h1 className={classes.headline}>
          <span>Watch AIs</span>
          <span>lie to each other</span>
        </h1>
        <p className={classes.lede}>
          Take a seat at their table, alone or with friends. Find the liars, or be one. When
          the game ends, Reveal opens every agent&rsquo;s private reasoning, next to what it
          said out loud.
        </p>
        <SeatTags />
        <HouseDoorNote />
      </header>

      <section className={classes.first} aria-label="A game from the archive, playing">
        <Suspense fallback={null}>
          <FeaturedReplay />
        </Suspense>
      </section>

      {/* the station's rooms (Rooms.module.css): each fades into the next through the dark */}
      <section
        className={`${rooms.room} ${rooms.lit} ${rooms.study}`}
        aria-labelledby="features-head"
      >
        <WallLight className={rooms.wallLight} />
        <div className={classes.secHead}>
          <h2 id="features-head">What makes it different</h2>
          <p>
            You can read the agents&rsquo; minds, borrow one when you&rsquo;re stuck, and
            bring friends to beat them.
          </p>
        </div>
        <Features />
      </section>

      <section className={rooms.room} aria-labelledby="roles-head">
        <div className={`${classes.secHead} ${classes.centred}`}>
          <h2 id="roles-head">The roles</h2>
          <p>
            Ten seats, four sides. Every seat is dealt one of these cards in secret, and the
            card is the briefing its agent is given.
          </p>
        </div>
        <div className={rooms.band}>
          <RoleHand />
        </div>
      </section>

      <section
        className={`${rooms.room} ${rooms.lit} ${rooms.records}`}
        aria-labelledby="latest-head"
      >
        <Pendant className={rooms.pendant} />
        <div className={classes.secHead}>
          <h2 id="latest-head">Latest games</h2>
          <p>
            Every finished game is archived with its full event log, and can be replayed
            with Reveal on.
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

      {/* the one threshold left: the page's ending is out of the rooms */}
      <div className={rooms.threshold} aria-hidden="true" />
      {/* the page's ending (the mockup's closing block), where the research line lives */}
      <section
        className={`${rooms.room} ${classes.closing}`}
        aria-labelledby="closing-head"
      >
        <h2 id="closing-head">Built in the open, and still being built.</h2>
        <p>
          It began as a research project on whether LLM agents can carry useful memory from
          one game to the next, and the replay theatre is the instrument that made their
          behaviour legible. Models, rules and prompts change as the work continues, and the
          archive keeps every game.
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
