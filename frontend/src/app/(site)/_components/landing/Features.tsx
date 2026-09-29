'use client';

/**
 * "What makes it different" (landing_features.md, on the landing's workshop bench): three paper
 * cards on the car's walnut, each under a brass plate with its number. Reading the agents'
 * minds and the lessons they weigh; borrowing your own agent to draft a line; bringing
 * friends to a table of agents. Each card leads with the feature and gives the mechanism
 * under it, in a line of its own.
 *
 * On a wide screen all three lie on the bench. Narrower (the bench's own width under 640px,
 * a container query) the plates become tabs and one card shows at a time, each at its own
 * height.
 */
import Link from 'next/link';
import { useId, useState, type CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { castForGame } from '@/stage/cast/castForGame';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { stageFonts } from '@/stage/fonts';
import {
  DRAFT,
  FEATURE_GAME,
  LOOP,
  NEVER_SEES,
  PLATES,
  ROOM_PEOPLE,
  SEES,
  TAUGHT,
  WEIGHED,
} from './features';
import classes from './Features.module.css';

const CAST = castForGame(FEATURE_GAME);

function Chip({ seat, className }: { seat: number; className?: string }) {
  return (
    <span className={className ?? classes.chip}>
      <ChipSprite character={CAST[seat - 1]} />
    </span>
  );
}

function Plate({ i }: { i: number }) {
  return (
    <div className={`${classes.plate} ${classes.brass}`}>
      <span className={classes.num}>{PLATES[i].num}</span>
      <span className={classes.cap}>{PLATES[i].cap}</span>
    </div>
  );
}

export function Features() {
  const ids = useId();
  const [card, setCard] = useState(0);

  const pick = (i: number) => setCard((i + PLATES.length) % PLATES.length);
  const sel = (i: number) => (i === card ? classes.sel : '');

  return (
    <div
      className={`${classes.shop} ${stageFonts}`}
      style={{ '--wood': `url(${SPRITES.wood.src})` } as CSSProperties}
    >
      <div
        className={classes.ptabs}
        role="tablist"
        aria-label="What makes it different"
        onKeyDown={(e) => {
          if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
          e.preventDefault();
          pick(card + (e.key === 'ArrowRight' ? 1 : -1));
        }}
      >
        {PLATES.map((p, i) => (
          <button
            key={p.tab}
            type="button"
            role="tab"
            id={`${ids}-tab${i}`}
            aria-selected={i === card}
            tabIndex={i === card ? 0 : -1}
            className={`${classes.ptab} ${classes.brass}`}
            onClick={() => pick(i)}
          >
            <span className={classes.num}>{p.num}</span>
            <span className={classes.cap}>{p.tab}</span>
          </button>
        ))}
      </div>

      <div className={classes.body}>
        <article className={`${classes.blk} ${classes.bMind} ${sel(0)}`}>
          <Plate i={0} />
          <h3>Read their minds, then watch them learn</h3>
          <p>
            The X-ray shows each agent&rsquo;s private reasoning beside what it said out
            loud: its notes, its read on every seat, the lessons it weighed before it spoke,
            and what the game taught it afterwards. Seat {WEIGHED.seat}, a wolf, in the game
            above:
          </p>
          <div className={classes.pair}>
            <div className={classes.slip}>
              <div className={classes.who}>
                <Chip seat={WEIGHED.seat} />
                Day 2, before the vote: a lesson it recalled
              </div>
              <p className={classes.typed}>{WEIGHED.lesson}</p>
              <span className={classes.stamp}>set aside</span>
              <p className={classes.why}>{WEIGHED.why}</p>
            </div>
            <span className={classes.arrow} aria-hidden="true" />
            <div className={classes.slip}>
              <div className={classes.who}>
                <Chip seat={WEIGHED.seat} />
                After the game: what it taught the wolf
              </div>
              <p className={classes.typed}>{TAUGHT}</p>
            </div>
          </div>
          <ol className={classes.loop}>
            {LOOP.map((l) => (
              <li key={l.step}>
                <b>{l.step}</b>
                {l.text}
              </li>
            ))}
          </ol>
          <p className={classes.how}>
            <b>How:</b> with memory on, the agents at the table draw on lessons from past
            games, gathered round this loop. Whether they win more because of it is the open
            research question.
          </p>
        </article>

        <article className={`${classes.blk} ${classes.bDraft} ${sel(1)}`}>
          <Plate i={1} />
          <h3>Stuck on your turn? Let your agent draft it</h3>
          <p>
            Jot rough notes and your seat&rsquo;s own agent turns them into a line, or hand
            it the whole turn: the vote, or the night&rsquo;s move.
          </p>
          <div className={classes.dock}>
            <div className={classes.jot}>
              <div className={classes.d}>Your notes</div>
              {DRAFT.notes}
            </div>
            <span className={classes.draftBtn} aria-hidden="true">
              Draft from notes
            </span>
            <div className={classes.line}>
              <Chip seat={DRAFT.seat} />
              <span>{DRAFT.line}</span>
            </div>
            <p className={classes.caption}>
              A real draft, from day 3 of the game above. Seat 8 was a wolf.
            </p>
          </div>
          <div className={classes.wall}>
            <div>
              <b>Your agent sees</b>
              <ul>
                {SEES.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
            <div>
              <b>It never sees</b>
              <ul className={classes.never}>
                {NEVER_SEES.map((s) => (
                  <li key={s}>{s}</li>
                ))}
              </ul>
            </div>
          </div>
          <p className={classes.how}>
            <b>How:</b> your agent is handed only what your seat is allowed to know. That
            wall is built where each agent&rsquo;s prompt is put together, not by asking the
            model to keep a secret, and every agent at the table stands behind the same one.
          </p>
        </article>

        <article className={`${classes.blk} ${classes.bRoom} ${sel(2)}`}>
          <Plate i={2} />
          <h3>Bring your friends. Beat the machines</h3>
          <p>
            Open a room, send the link, and your friends take seats at a table of agents.
            Agents fill every place still empty when the game starts.
          </p>
          <div className={classes.roster} aria-hidden="true">
            {ROOM_PEOPLE.map((name) => (
              <span key={name} className={classes.person}>
                <i>{name[0]}</i>
                {name}
              </span>
            ))}
            {[4, 5, 6, 7, 8, 9].map((seat) => (
              <span key={seat} className={classes.person}>
                <Chip seat={seat} className={classes.agent} />
                agent
              </span>
            ))}
          </div>
          <div className={classes.invite} aria-hidden="true">
            <b>Invite</b>
            <span>the room&rsquo;s link, for anyone you send it to</span>
            <i>Copy</i>
          </div>
          <p className={classes.how}>
            <b>How:</b> every seat gets the game live, each seeing only its own side of it.
            If someone goes quiet, their clock runs out and their own agent takes the turn,
            so the table never stalls.
          </p>
          <Link href="/rooms/new" className={classes.open}>
            Open a table &rarr;
          </Link>
        </article>
      </div>
    </div>
  );
}
