import { Suspense } from 'react';
import Link from 'next/link';
import { Anchor } from '@mantine/core';
import { Button, GuideSign } from '@/components/site';
import { Pendant, WallLight } from '@/components/site/StationLamps';
import { SITE } from '@/lib/site';
import { PageMusic } from '@/music/PageMusic';
import { stageFonts } from '@/stage/fonts';
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
 * The landing (landing mockup, review §A1, rulings §F7; reworked with the owner 2026-10-15 and
 * 2026-10-16): the hero (the game's name as its sign, the hook, the two hung tags), a game from
 * the archive playing in the carriage, the story and then what makes it different, the replay (one real moment of a bluff, then the latest games), and a closing on
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
      {/* the guide's piece, for a viewer who turns it on (the nav's switch) */}
      <PageMusic bed="guide" />
      <header className={classes.hero}>
        {/* the game's name is the sign, the hook its tagline (owner, 2026-10-16) */}
        <h1 className={classes.name}>The Ninth Express</h1>
        <p className={classes.tagline}>Watch AIs lie to each other</p>
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
        {/* the story, told inside the train in its voice, then, set apart in the site's, the
            promise (owner, 2026-10-15; out of the hero into this room, 2026-10-16) */}
        <div className={`${classes.prologue} ${stageFonts}`}>
          <p className={classes.tale}>
            Aboard The Ninth Express, the killers are part of the conversation. Ten puppets
            share a carriage, but not a destination. Wolves sit among the passengers, a lone
            killer watches for an opening, and someone has a wager of their own.
          </p>
          <p className={classes.tale}>
            Every passenger has a story to tell, and a secret worth protecting. Question
            their stories, conceal your own, and decide whom to trust.
          </p>
          <p className={classes.promise}>
            When the journey ends, Reveal lets you glimpse their private notes&mdash;and
            discover what was hiding behind their words.
          </p>
        </div>
        {/* the room's one light hangs by the start of the features (Rooms.module.css) */}
        <div className={rooms.lamplit}>
          <WallLight className={rooms.wallLight} />
          <div className={classes.secHead}>
            <h2 id="features-head">What makes it different</h2>
          </div>
          <Features />
        </div>
      </section>

      <section
        className={`${rooms.room} ${rooms.lit} ${rooms.records}`}
        aria-labelledby="replay-head"
      >
        <Pendant className={rooms.pendant} />
        {/* the reveal the story promises, shown: one real moment, then the games to open */}
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
        {/* Two research threads: learning across games and reasoning within a game. */}
        <h2 id="closing-head">Can smaller models become better players?</h2>
        <p>
          Werewolf puts memory and reasoning under pressure. Agents must act on incomplete
          information while other players deliberately mislead them. In our games, smaller
          models also miss connections between clues, misread results and invent facts—even
          when the evidence they need is already in front of them.
        </p>
        <p>
          This project explores how experience and reasoning support can help them make
          better decisions without retraining their underlying models.
        </p>
        <div className={classes.researchThreads}>
          <section
            className={classes.researchThread}
            aria-labelledby="memory-research-head"
          >
            <h3 id="memory-research-head">Learn from past games</h3>
            <p>
              A memory pipeline extracts observations from past games and uses a stronger
              model to turn them into reusable strategies. Agents retrieve relevant lessons
              when they face a new situation. The aim is to carry useful reasoning from a
              stronger model into a smaller model&rsquo;s decisions, as well as preserve
              experience across games.
            </p>
          </section>
          <section
            className={classes.researchThread}
            aria-labelledby="deduction-research-head"
          >
            <h3 id="deduction-research-head">Connect the evidence in this game</h3>
            <p>
              Remembering a lesson still leaves the agent with deductions to make. Seeing
              someone visit a player, for example, does not prove they healed them. We are
              developing rule-based support that makes the implications of public events and
              an agent&rsquo;s own results explicit, with player claims and conditional
              conclusions identified as such.
            </p>
          </section>
        </div>
        <p>
          <strong className={classes.pivot}>
            The challenge is finding out which help actually improves decisions.
          </strong>{' '}
          A winning game can hide bad decisions, and a plausible reflection can reinforce
          the wrong strategy. Strategies are scored against games where they were used;
          recorded decisions, replay tools and controlled evaluations let us inspect where
          both memory and reasoning support help or fail.
        </p>
        {/* the state of the work, by the way to its evidence */}
        <div className={classes.standing}>
          <p>
            The memory pipeline is built, and deduction support is being developed and
            tested. Earlier memory experiments found both gains and failures. Whether the
            current system reliably improves play at scale remains an open question.
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
