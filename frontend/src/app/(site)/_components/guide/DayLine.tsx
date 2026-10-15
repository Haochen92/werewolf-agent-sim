'use client';

/**
 * A day, phase by phase, as a railway line: a stop per phase on a brass track, dawn gold to
 * night blue and back, the end of the game its terminus. A small engine runs to the stop
 * picked; the stop's card is the site's walnut signboard, with the phase's own instrument
 * working in one fixed slot (so stepping along the line moves no edge), and your part on a cream
 * plate. Under the line, the clock's enamel sign.
 */
import type { ComponentType, CSSProperties, ReactNode } from 'react';
import { DiscGlyph } from '@/stage/instruments/TopStrip';
import { ClockSign } from './ClockSign';
import {
  DiscussionDemo,
  EndingDemo,
  LastWordDemo,
  MorningDemo,
  NightDemo,
  OpeningDemo,
  VoteDemo,
} from './StopDemos';
import { useTabs } from './useTabs';
import guide from './Guide.module.css';
import classes from './DayLine.module.css';

type Disc = 'sun' | 'moon' | 'end';

const STOPS: {
  id: string;
  name: string;
  disc: Disc;
  Demo: ComponentType;
  text: ReactNode;
  you?: ReactNode;
}[] = [
  {
    id: 'opening',
    name: 'Opening round',
    disc: 'sun',
    Demo: OpeningDemo,
    text: 'Every living seat writes an opening at the same time; then they are read out in seat order. On day 1 this is the only round.',
    you: 'claim a role, share what you learned last night, challenge someone, or pass.',
  },
  {
    id: 'discussion',
    name: 'Discussion',
    disc: 'sun',
    Demo: DiscussionDemo,
    text: 'Anyone asked a question or accused answers first. Then the floor goes, in seat order, to the seats that have not spoken today.',
    you: 'write your line and send it, or pass.',
  },
  {
    id: 'lastword',
    name: 'Last word',
    disc: 'sun',
    Demo: LastWordDemo,
    text: 'Before the vote, any seat accused by two or more others gets a last word: at most two seats, written at the same time.',
    you: <>make your case, if it&rsquo;s you.</>,
  },
  {
    id: 'vote',
    name: 'Vote',
    disc: 'sun',
    Demo: VoteDemo,
    text: 'Everyone votes at once, in secret. The seat with the most votes is out and its card is turned; a tie sends nobody out. After two days in a row with nobody out, abstaining is off.',
    you: <>tap a seat&rsquo;s chip, or the empty plate to abstain.</>,
  },
  {
    id: 'night',
    name: 'Night',
    disc: 'moon',
    Demo: NightDemo,
    text: 'Each role acts alone, in its own room. The wolves talk in private; one names the kill, then each uses its own skill.',
    you: 'pick a photo on the wall and confirm. Your card says what your role does.',
  },
  {
    id: 'morning',
    name: 'Morning',
    disc: 'sun',
    Demo: MorningDemo,
    text: 'The morning roll names who died in the night, what killed them, and their role, and anyone attacked and saved. A concealed victim’s role stays hidden. Then the next day opens, and so on until one side has won.',
  },
  {
    id: 'end',
    name: 'End game',
    disc: 'end',
    Demo: EndingDemo,
    text: 'The game ends the moment one side has won: after a vote, or at a morning. Every card turns face up, and the box tells you who won, and how you did.',
    you: 'watch the replay, or go back to the lobby.',
  },
];
const IDS = STOPS.map((s) => s.id);
/** The numbered stops: the terminus has none. */
const NUMBERED = STOPS.filter((s) => s.disc !== 'end').length;

/** The terminus: a buffer stop on the rails. */
function BufferStop() {
  return (
    <svg className={classes.buffer} viewBox="0 0 24 24" aria-hidden="true">
      <path d="M3 20h18" />
      <path d="M6 20V9M18 20V9" />
      <rect x="4" y="6" width="16" height="4" rx="1" />
      <circle cx="8" cy="8" r="1.4" />
      <circle cx="16" cy="8" r="1.4" />
    </svg>
  );
}

/** A small engine, facing down the line. */
function Engine() {
  return (
    <svg viewBox="0 0 52 30">
      <path d="M29 3h17v4h-2v13H29z" />
      <rect className={classes.dark} x="33" y="8" width="7" height="6" rx="1" />
      <path d="M7 11h23v9H7z" />
      <rect x="10" y="3" width="6" height="9" rx="1" />
      <path d="M8.5 3h9v2h-9z" />
      <circle cx="23" cy="11" r="3.2" />
      <path d="M2 21l5-7v7z" />
      <path d="M3 20h45v3H3z" />
      <circle cx="13" cy="24.5" r="4.5" />
      <circle cx="24" cy="24.5" r="4.5" />
      <circle cx="38" cy="25" r="3.5" />
      <circle className={classes.dark} cx="13" cy="24.5" r="1.4" />
      <circle className={classes.dark} cx="24" cy="24.5" r="1.4" />
      <circle className={classes.dark} cx="38" cy="25" r="1.1" />
    </svg>
  );
}

export function DayLine() {
  const t = useTabs(IDS);
  return (
    <>
      <div
        className={classes.route}
        role="tablist"
        aria-label="The stops of a day"
        style={{ '--n': STOPS.length, '--at': t.index } as CSSProperties}
      >
        <span className={classes.track} aria-hidden="true" />
        <span className={classes.engine} aria-hidden="true">
          <Engine />
        </span>
        {STOPS.map((s, i) => (
          <button key={s.id} {...t.tab(s.id)}>
            <span className={classes.dot} data-disc={s.disc}>
              {s.disc === 'end' ? <BufferStop /> : i + 1}
            </span>
            <span className={classes.name}>{s.name}</span>
          </button>
        ))}
      </div>

      <div className={guide.stack}>
        {STOPS.map((s, i) => {
          const next = STOPS[(i + 1) % STOPS.length];
          return (
            <article key={s.id} className={classes.stop} {...t.panel(s.id)}>
              <header className={classes.head}>
                <span className={classes.disc} data-disc={s.disc} aria-hidden="true">
                  {s.disc === 'end' ? <BufferStop /> : <DiscGlyph kind={s.disc} />}
                </span>
                <h3>{s.name}</h3>
                <span className={classes.of}>
                  {s.disc === 'end' ? 'End of the line' : `${i + 1} of ${NUMBERED}`}
                </span>
              </header>
              <div className={classes.live}>
                <s.Demo />
              </div>
              <div className={classes.words}>
                <p>{s.text}</p>
                {s.you && (
                  <p className={classes.you}>
                    <b>You</b> {s.you}
                  </p>
                )}
                <button
                  type="button"
                  className={classes.next}
                  onClick={() => t.pick(next.id, true)}
                >
                  {i === STOPS.length - 1
                    ? 'Back to the first stop'
                    : `Next stop: ${next.name}`}{' '}
                  &rarr;
                </button>
              </div>
            </article>
          );
        })}
      </div>

      <ClockSign />
    </>
  );
}
