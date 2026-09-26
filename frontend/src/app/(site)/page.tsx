import { Suspense } from 'react';
import Link from 'next/link';
import { ReplayListClient } from './replays/_components/ReplayListClient';
import { HouseDoorNote } from './_components/HouseDoorNote';
import classes from './page.module.css';

/**
 * Landing (D1). A recruiter with zero context must reach the X-ray in two clicks, so
 * "watch a replay" is visually primary — it needs no key and no waiting — and the latest
 * replays sit right below as a rail that deep-links straight into the theater. No
 * screenshots or marketing sections: the replay rail IS the demo.
 *
 * All three doors are live as of the P2/P3 build. The two playing doors carry the
 * house's purse (HouseDoorNote): since the server gained a daily funding cap, whether a
 * visitor needs their own API key is state, and the door is the honest place to say it.
 */
export default function HomePage() {
  return (
    <main className={classes.page}>
      <section className={classes.hero}>
        <h1 className={classes.heroTitle}>
          Watch AIs deceive each other — and see exactly why.
        </h1>
        <p className={classes.heroLead}>
          Nine LLM agents play werewolf: they scheme, lie, build cases and vote each other
          out. When a game ends, the X-ray opens every agent’s private reasoning — including
          the lines a novelty gate stopped them from saying.
        </p>
      </section>

      <div className={classes.doors}>
        <Link href="/replays" className={`${classes.door} ${classes.doorPrimary}`}>
          <h2 className={classes.doorTitle}>Watch a replay</h2>
          <p className={classes.doorBody}>
            A finished game, start to finish, with the X-ray. No sign-up, no API key,
            nothing to wait for.
          </p>
        </Link>
        <Link href="/play" className={classes.door}>
          <h2 className={classes.doorTitle}>Quick game</h2>
          <p className={classes.doorBody}>
            Take a seat against eight agents. Pick a role or let the deal decide.
          </p>
          <HouseDoorNote />
        </Link>
        <Link href="/rooms" className={classes.door}>
          <h2 className={classes.doorTitle}>Rooms</h2>
          <p className={classes.doorBody}>
            Play with other people. Open a table and share the link.
          </p>
          <HouseDoorNote />
        </Link>
      </div>

      <div className={classes.sectionHead}>
        <h2 className={classes.sectionTitle}>Latest games</h2>
        <Link href="/replays" className={classes.sectionLink}>
          all replays →
        </Link>
      </div>
      <Suspense fallback={<div className={classes.skeletonCard} />}>
        <ReplayListClient limit={6} />
      </Suspense>

      <footer className={classes.footer}>
        A research project on whether LLM agents can accumulate useful memory across games.
        The replay theater is the instrument that made the behaviour legible.{' '}
        <a
          className={classes.footerLink}
          href="https://github.com/Haochen92/werewolf-agent-sim"
          target="_blank"
          rel="noreferrer"
        >
          Source on GitHub →
        </a>
      </footer>
    </main>
  );
}
