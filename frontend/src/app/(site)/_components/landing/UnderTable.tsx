'use client';

/**
 * "What's under the table" (the landing's workshop, bench 77): three paper cards on the car's
 * walnut, each under a brass plate with its number. Seat 8's private note on each day; every
 * read in the game as a dot, sure against unsure; and the lines the novelty gate held back.
 *
 * On a wide screen all three lie on the bench. Narrower (the bench's own width under 640px,
 * a container query) the plates become tabs and one card shows at a time, at one reserved
 * height so nothing below jumps; the notes get a row of days to pick one.
 */
import { useId, useState, type CSSProperties } from 'react';
import { SPRITES } from '@/assets/manifest';
import { castForGame } from '@/stage/cast/castForGame';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { stageFonts } from '@/stage/fonts';
import {
  DAY3_HELD,
  HELD,
  NOTE_SEAT,
  NOTES,
  PLATES,
  READ_MARKS,
  READS,
  UNDER_GAME,
  type ReadMark,
} from './under-table';
import classes from './UnderTable.module.css';

const CAST = castForGame(UNDER_GAME);

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

function Dots({
  counts,
  size,
}: {
  counts: Record<ReadMark, number>;
  size: 'sure' | 'unsure';
}) {
  return (
    <div className={`${classes.dots} ${classes[size]}`} aria-hidden="true">
      {READ_MARKS.flatMap((mark) =>
        Array.from({ length: counts[mark] }, (_, n) => (
          <i key={`${mark}${n}`} className={classes[mark]} />
        )),
      )}
    </div>
  );
}

const total = (c: Record<ReadMark, number>) => READ_MARKS.reduce((n, m) => n + c[m], 0);

export function UnderTable() {
  const ids = useId();
  const [card, setCard] = useState(0);
  const [day, setDay] = useState(4);
  const unsure = total(READS.unsure);

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
        aria-label="What's under the table"
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
        <article className={`${classes.blk} ${classes.bNote} ${sel(0)}`}>
          <Plate i={0} />
          <h3>It keeps a private note</h3>
          <p>
            After every turn an agent rewrites a note to itself. Nobody else sees it until
            the game ends. Here is seat {NOTE_SEAT}, the wolf, on each of the four days.
          </p>
          <div className={classes.daytabs} role="group" aria-label="Day">
            {NOTES.map((n) => (
              <button
                key={n.day}
                type="button"
                aria-pressed={n.day === day}
                onClick={() => setDay(n.day)}
              >
                Day {n.day}
              </button>
            ))}
          </div>
          <div className={classes.notes}>
            {NOTES.map((n) => (
              <div
                key={n.day}
                className={`${classes.note} ${n.day === day ? classes.sel : ''}`}
                style={{ '--r': n.tilt } as CSSProperties}
              >
                <Chip seat={NOTE_SEAT} className={classes.pin} />
                <div className={classes.d}>Day {n.day}</div>
                {n.text}
              </div>
            ))}
          </div>
        </article>

        <article className={`${classes.blk} ${classes.bReads} ${sel(1)}`}>
          <Plate i={1} />
          <h3>It keeps a read on everyone</h3>
          <p>
            Each agent guesses every other seat&rsquo;s role and says how sure it is. When
            it was sure, it was almost always right. When it wasn&rsquo;t, it mostly had no
            read at all.
          </p>
          <div className={classes.graph}>
            <div className={classes.waffle}>
              <div className={classes.g}>
                <b>Sure</b>
                {total(READS.sure)} reads
              </div>
              <Dots counts={READS.sure} size="sure" />
              <div className={`${classes.g} ${classes.ug}`}>
                <b>Unsure</b>
                {unsure} reads
              </div>
              <Dots counts={READS.unsure} size="unsure" />
              <div className={classes.ubar} aria-hidden="true">
                {READ_MARKS.map((m) => (
                  <span
                    key={m}
                    className={classes[m]}
                    style={{ width: `${((READS.unsure[m] / unsure) * 100).toFixed(2)}%` }}
                  />
                ))}
              </div>
              <div className={classes.ucap}>
                <b>Unsure, {unsure} reads:</b> {READS.unsure.right} role right,{' '}
                {READS.unsure.side} right side, {READS.unsure.wrong} wrong,{' '}
                {READS.unsure.none} no read
              </div>
            </div>
          </div>
          <div className={classes.legend}>
            <span>
              <i className={classes.right} />
              role right
            </span>
            <span>
              <i className={classes.side} />
              right side
            </span>
            <span>
              <i className={classes.wrong} />
              wrong
            </span>
            <span>
              <i className={classes.none} />
              no read
            </span>
          </div>
        </article>

        <article className={`${classes.blk} ${classes.bGate} ${sel(2)}`}>
          <Plate i={2} />
          <h3>It can&rsquo;t repeat itself</h3>
          <p>
            A line too close to what the table has already heard is held back, and the agent
            passes instead. Seat {HELD.seat} on day 4, the day after the vote above:
          </p>
          <div className={classes.held}>
            <div className={classes.who}>
              <Chip seat={HELD.seat} />
              Seat {HELD.seat}, drafted
            </div>
            <s>{HELD.text}</s>
            <span className={classes.stamp}>held back</span>
          </div>
          <div className={classes.then}>
            <Chip seat={HELD.seat} />
            Seat {HELD.seat} passes.
          </div>
          <div className={classes.row5}>
            <span className={classes.lbl}>Day 3: five held back in a row</span>
            {DAY3_HELD.map(([seat, start]) => (
              <div key={seat} className={classes.r}>
                <Chip seat={seat} />
                <s>{start}&hellip;</s>
              </div>
            ))}
            <div className={classes.strip} aria-hidden="true">
              {DAY3_HELD.map(([seat]) => (
                <Chip key={seat} seat={seat} />
              ))}
            </div>
          </div>
        </article>
      </div>
    </div>
  );
}
