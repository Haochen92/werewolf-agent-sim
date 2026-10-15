'use client';

/**
 * "What makes it different" (owner, 2026-10-15): three paper cards on the car's walnut, each
 * under a brass plate with its name. Agents that bring lessons from past games, and whether
 * they follow them; your own agent drafting your case; a table that plays on when someone
 * leaves. Each card is the claim and one picture of it, a real moment where there is one.
 *
 * On a wide screen all three lie on the bench, side by side. Narrower (the bench's own width under 640px,
 * a container query) the plates become tabs and one card shows at a time, each at its own
 * height.
 */
import Link from 'next/link';
import { useId, useState, type CSSProperties } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { Button } from '@/components/site';
import { castForGame, resolveCast } from '@/stage/cast/castForGame';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { stageFonts } from '@/stage/fonts';
import { SITE } from '@/lib/site';
import { DRAFT, LESSON, PLATES, ROOM_PEOPLE } from './features';
import classes from './Features.module.css';

/** Each card's seats are its own game's cast. */
const LESSON_CAST = resolveCast(LESSON.cast, LESSON.game, 10);
const DRAFT_CAST = castForGame(DRAFT.game);
const ROOM_CAST = castForGame(SITE.featuredReplay, 10);

function Chip({ character, className }: { character: Character; className?: string }) {
  return (
    <span className={className ?? classes.chip}>
      <ChipSprite character={character} />
    </span>
  );
}

function Plate({ i }: { i: number }) {
  return (
    <div className={`${classes.plate} ${classes.brass}`}>
      <span className={classes.num}>{PLATES[i]}</span>
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
            key={p}
            type="button"
            role="tab"
            id={`${ids}-tab${i}`}
            aria-selected={i === card}
            tabIndex={i === card ? 0 : -1}
            className={`${classes.ptab} ${classes.brass}`}
            onClick={() => pick(i)}
          >
            <span className={classes.num}>{p}</span>
          </button>
        ))}
      </div>

      <div className={classes.body}>
        <article className={`${classes.blk} ${classes.bMind} ${sel(0)}`}>
          <Plate i={0} />
          <h3>They bring lessons from past games</h3>
          <p>
            With memory on, agents retrieve strategies from earlier games that fit their role
            and situation. In the replay, see which lessons each one weighed, and whether it
            followed them or overrode them.
          </p>
          <div className={classes.slip}>
            <div className={classes.who}>
              <Chip character={LESSON_CAST[LESSON.seat - 1]} />
              Night 2, Seat {LESSON.seat}, the Sigilist: a lesson it recalled
            </div>
            <p className={classes.typed}>{LESSON.lesson}</p>
            <span className={classes.stamp}>followed</span>
            <p className={classes.why}>{LESSON.why}</p>
          </div>
          <p className={classes.result}>
            <Chip character={LESSON_CAST[LESSON.struck - 1]} />
            <span>
              That night Seat {LESSON.struck}, the Chanteuse, attacked, and the sigil struck it
              down.
            </span>
          </p>
        </article>

        <article className={`${classes.blk} ${classes.bDraft} ${sel(1)}`}>
          <Plate i={1} />
          <h3>Make your case without typing every word</h3>
          <p>
            Give your agent a few rough notes and let it draft your response. You can also
            hand over a turn entirely, a vote or a night action included. It works with what
            your seat knows.
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
              <Chip character={DRAFT_CAST[DRAFT.seat - 1]} />
              <span>{DRAFT.line}</span>
            </div>
            <p className={classes.caption}>
              The notes were written for this demo; the line is what an agent drafted from them,
              mid-game, in an archived game.
            </p>
          </div>
        </article>

        <article className={`${classes.blk} ${classes.bRoom} ${sel(2)}`} data-surface="paper">
          <Plate i={2} />
          <h3>Someone leaves. The game goes on</h3>
          <p>
            Invite friends and let agents fill the remaining seats. If someone disconnects or
            misses their turn, their agent takes over when the timer runs out, so the rest of
            you keep playing.
          </p>
          <div className={classes.roster} aria-hidden="true">
            {ROOM_PEOPLE.map((name, i) => (
              <span
                key={name}
                className={classes.person}
                data-lapsed={i === ROOM_PEOPLE.length - 1 || undefined}
              >
                <i>{name[0]}</i>
                {name}
              </span>
            ))}
            {[4, 5, 6, 7, 8, 9, 10].map((seat) => (
              <span key={seat} className={classes.person}>
                <Chip character={ROOM_CAST[seat - 1]} className={classes.agent} />
                agent
              </span>
            ))}
          </div>
          <p className={classes.lapse}>
            <span className={classes.timer} aria-hidden="true" />
            Sam&rsquo;s timer ran out: Sam&rsquo;s agent takes the turn.
          </p>
          <Button component={Link} href="/rooms/new" size="sm" className={classes.open}>
            Open a table &rarr;
          </Button>
        </article>
      </div>
    </div>
  );
}
