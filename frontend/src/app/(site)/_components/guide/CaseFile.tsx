'use client';

/**
 * After the game, as the game's case file: a kraft folder with an index tab per part (the
 * replay, Reveal, the transcript, memory). Each part is an exhibit clipped in, working, beside a
 * ruled index card that says what it is; the replay's slate sits beside its card, its controls
 * run under both. The three panels fed from recorded games load with their fixtures, lazily.
 */
import dynamic from 'next/dynamic';
import type { ReactNode } from 'react';
import { Slate } from '@/components/site';
import type { ReplaySummary } from '@/types/contracts';
import { ReplayDemo } from './StopDemos';
import { useTabs } from './useTabs';
import guide from './Guide.module.css';
import classes from './CaseFile.module.css';

const RevealDemo = dynamic(() => import('./ExhibitDemos').then((m) => m.RevealDemo), {
  ssr: false,
});
const TranscriptDemo = dynamic(
  () => import('./ExhibitDemos').then((m) => m.TranscriptDemo),
  {
    ssr: false,
  },
);
const MemoryDemo = dynamic(() => import('./ExhibitDemos').then((m) => m.MemoryDemo), {
  ssr: false,
});

/** The slate of a finished game, as the archive files it (the guide's: it goes nowhere). */
const SLATE: ReplaySummary = {
  game_id: 'c41e07b2-5d1a-4c2e-9f3b-2a7e8d6c1f04',
  finished_at: '2026-09-24T19:42:00Z',
  winner: 'villagers',
  days: 3,
  ended_phase: 'voting',
  n_events: 412,
  n_humans: 1,
  cast_role_counts: {
    investigator: 1,
    sentinel: 1,
    trailseer: 1,
    vigilante: 1,
    sigilist: 1,
    healer: 1,
    chanteuse: 1,
    illusionist: 1,
    serial_killer: 1,
    fortune_teller: 1,
  },
  model: 'gemini-3.5-flash',
  memory: true,
  cost_usd: 0.27,
  avg_call_seconds: 4.1,
} as ReplaySummary;

const TABS = [
  ['replay', 'Replay'],
  ['reveal', 'Reveal'],
  ['transcript', 'Transcript'],
  ['memory', 'Memory'],
] as const;

function IndexCard({
  title,
  stamp,
  children,
}: {
  title: string;
  stamp?: string;
  children: ReactNode;
}) {
  return (
    <div className={classes.card}>
      {stamp && (
        <span className={classes.stamp} aria-hidden="true">
          {stamp}
        </span>
      )}
      <h3>{title}</h3>
      <ul>{children}</ul>
    </div>
  );
}

function Paperclip() {
  return <span className={classes.paperclip} aria-hidden="true" />;
}

export function CaseFile() {
  const t = useTabs(TABS.map(([id]) => id));
  return (
    <div className={classes.folder}>
      <div className={classes.tabs} role="tablist" aria-label="After the game">
        {TABS.map(([id, name]) => (
          <button key={id} {...t.tab(id)}>
            {name}
          </button>
        ))}
      </div>
      <div className={`${guide.stack} ${classes.body}`}>
        <article className={`${classes.file} ${classes.replay}`} {...t.panel('replay')}>
          <div className={`${classes.clip} ${classes.slate}`}>
            {/* the archive's own slate, shown: a link to a game the guide made up would go nowhere */}
            <div className={classes.slateBox} inert>
              <Slate replay={SLATE} modelLabel="Gemini 3.5 Flash" />
            </div>
            <Paperclip />
          </div>
          <IndexCard title="The replay">
            <li>Open it from the end screen, or find its slate in the archive.</li>
            <li>
              Until it is filed the end screen says <b>Winding the reels&hellip;</b>: come
              back in a few minutes.
            </li>
            <li>
              Jump a chapter, step a beat, or play it through, at normal or fast speed.
            </li>
          </IndexCard>
          <div className={`${classes.clip} ${classes.band}`}>
            <ReplayDemo />
          </div>
        </article>

        <article className={classes.file} {...t.panel('reveal')}>
          <div className={`${classes.clip} ${classes.live}`}>
            <RevealDemo />
          </div>
          <IndexCard title="Reveal and the case file">
            <li>
              <b>Reveal</b> shows what was hidden: every role, the night acts, the
              wolves&rsquo; talk, why a seat passed.
            </li>
            <li>
              Tap a seat for its case file: <b>Notes</b>, its private plan page by page;{' '}
              <b>Reads</b>, who it suspected, checked against the truth.
            </li>
            <li>
              Without Reveal, the case file shows the record: each morning&rsquo;s
              accusations and claims.
            </li>
          </IndexCard>
        </article>

        <article className={classes.file} {...t.panel('transcript')}>
          <div className={`${classes.clip} ${classes.live}`}>
            <TranscriptDemo />
            <Paperclip />
          </div>
          <IndexCard title="The transcript">
            <li>Everything said, under a heading per day.</li>
            <li>
              Filter by day or by seat. A seated player, or anyone with Reveal on, can show
              the private lines.
            </li>
            <li>In a replay it stops where you are: nothing is spoiled.</li>
          </IndexCard>
        </article>

        <article className={classes.file} {...t.panel('memory')}>
          <div className={`${classes.clip} ${classes.live}`}>
            <MemoryDemo />
            <Paperclip />
          </div>
          <IndexCard title="Memory-on games" stamp="Memory on">
            <li>
              <b>Agents&rsquo; memory</b> on the ticket, when the house allows it. Off by
              default: every agent plays fresh.
            </li>
            <li>
              A seat&rsquo;s <b>Lessons</b> tab: the lesson it looked up, stamped Followed,
              Overrode or Doesn&rsquo;t apply, with why.
            </li>
            <li>
              Its <b>Findings</b> tab: each role&rsquo;s account of its play, written after
              the game, offline. Until then the end screen says the lessons are being
              written.
            </li>
          </IndexCard>
        </article>
      </div>
    </div>
  );
}
