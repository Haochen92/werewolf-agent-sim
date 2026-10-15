import { Suspense } from 'react';
import Link from 'next/link';
import { Anchor } from '@mantine/core';
import { Button, GuideSign } from '@/components/site';
import { Pendant, WallLight } from '@/components/site/StationLamps';
import { SITE } from '@/lib/site';
import { ReplayListClient } from './replays/_components/ReplayListClient';
import { HouseDoorNote } from './_components/HouseDoorNote';
import { SeatTags } from './_components/landing/SeatTags';
import { FeaturedReplay } from './_components/landing/FeaturedReplay';
import { PlatformBackdrop } from './_components/landing/PlatformBackdrop';
import platform from './_components/landing/PlatformBackdrop.module.css';
import { Features } from './_components/landing/Features';
import { ReplayMoment } from './_components/landing/ReplayMoment';
import { BLUFF } from './_components/landing/features';
import rooms from './_components/landing/Rooms.module.css';
import classes from './_components/landing/Landing.module.css';
import pageClasses from './page.module.css';

/**
 * The landing (landing mockup, review §A1, rulings §F7; reworked with the owner 2026-10-15): the
 * hero with its two hung tags, a game from the archive playing in the carriage, what makes it
 * different, the replay (one real moment of a bluff, then the latest games), and a closing on
 * the research behind it. A recruiter with no context sees the product working before reading
 * a word, and reaches a whole replay in one click from the carriage. The roles live on `/guide`.
 *
 * Under the carriage each section is a room of the station (Rooms.module.css), one running into
 * the next through the dark: granite under a caged wall light, then the platform's tile under a
 * pendant. The way to play is the hero's tags and the nav.
 *
 * The two playing doors carry the house's purse (HouseDoorNote): whether a visitor needs their
 * own API key is live state, and the door is the honest place to say it.
 */
export default function HomePage() {
  return (
    <main className={`${classes.landing} ${platform.scene} ${platform.heroScene}`}>
      <PlatformBackdrop />
      <header className={classes.hero}>
        <h1 className={classes.headline}>
          <span>Watch AIs</span>
          <span>lie to each other</span>
        </h1>
        {/* the setting and your part in it, then, set apart, the promise (owner, 2026-10-15) */}
        <p className={classes.lede}>
          Aboard The Ninth Express, the killers are part of the conversation. Every
          passenger has a story to tell, and a secret worth protecting. Question their
          stories, conceal your own, and decide whom to trust.
        </p>
        <p className={`${classes.lede} ${classes.reveal}`}>
          When the journey ends, Reveal lets you glimpse their private notes&mdash;and
          discover what was hiding behind their words.
        </p>
        <SeatTags />
        <HouseDoorNote />
        {/* the guide is something to read, so its sign and not a third tag (owner, 2026-10-15) */}
        <GuideSign className={classes.heroGuide} />
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
        </div>
        <Features />
      </section>

      <section
        className={`${rooms.room} ${rooms.lit} ${rooms.records}`}
        aria-labelledby="replay-head"
      >
        <Pendant className={rooms.pendant} />
        {/* the reveal the hero promises, shown: one real moment, then the games to open */}
        <div className={classes.replay}>
          <div className={classes.pitch}>
            <h2 id="replay-head">At the end of the line, the secrets come out</h2>
            <p>
              Was that accusation an honest suspicion or a deliberate bluff? Open a replay
              and follow each agent&rsquo;s private reasoning as the game unfolds, next to
              what it told the table.
            </p>
            <p>
              Read its suspicions, its plans, and the lessons it weighed from past games.
            </p>
            <Button
              component={Link}
              href={`/replays/${BLUFF.game}?from=home`}
              variant="plate"
            >
              Explore this replay &rarr;
            </Button>
          </div>
          <ReplayMoment />
        </div>
        <h3 id="latest-head" className={classes.latestHead}>
          Latest games
        </h3>
        {/* two rows of two; one column of two where the grid goes single file */}
        <div className={classes.latest}>
          <Suspense fallback={<div className={pageClasses.skeletonCard} />}>
            <ReplayListClient limit={4} />
          </Suspense>
        </div>
        <Anchor component={Link} href="/replays" className={classes.allGames}>
          All replays &rarr;
        </Anchor>
      </section>

      {/* the one threshold left: the page's ending is out of the rooms */}
      <div className={rooms.threshold} aria-hidden="true" />
      {/* the page's ending (the mockup's closing block), where the research line lives */}
      <section
        className={`${rooms.room} ${classes.closing}`}
        aria-labelledby="closing-head"
      >
        {/* motivation, mechanism, the hard part, where it stands (owner, 2026-10-15) */}
        <h2 id="closing-head">Can agents turn experience into better decisions?</h2>
        <p>
          Social deduction games like Werewolf put memory and reasoning under pressure:
          agents must act on incomplete information while other players deliberately mislead
          them. Without memory, every game starts from scratch: what the agents learned in
          earlier games is lost.
        </p>
        <p>
          This project explores whether agents can build useful experience without
          retraining their underlying models. Its memory pipeline extracts observations from
          past games, consolidates them into strategies, and retrieves those relevant to a
          new situation. It scores each strategy against the games where it was used, and
          prunes those with poor records.
        </p>
        <p>
          <strong className={classes.pivot}>
            The challenge is deciding what counts as a useful lesson.
          </strong>{' '}
          A winning game can hide bad decisions, and a plausible reflection can reinforce
          the wrong strategy. Recorded decisions, replay tools and controlled evaluations
          make those failures inspectable.
        </p>
        {/* the state of the work, by the way to its evidence */}
        <div className={classes.standing}>
          <p>
            The pipeline is built. Controlled experiments on earlier versions found both
            gains and failures, and those findings shaped the current version, which
            hasn&rsquo;t yet been tested at scale. Whether it improves play is still an open
            question.
          </p>
          <Button
            component="a"
            href={SITE.caseStudy}
            target="_blank"
            rel="noreferrer"
            variant="plate"
          >
            Read the case study &rarr;
          </Button>
        </div>
      </section>
    </main>
  );
}
