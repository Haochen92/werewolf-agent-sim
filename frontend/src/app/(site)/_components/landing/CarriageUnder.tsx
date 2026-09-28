'use client';

/**
 * The carriage's controls on an upright phone (landing mockup, "narrow"): there the stage is
 * a quarter of its size and its words cannot be read, so they leave it and sit under it at
 * reading size. A bar (play or pause, where we are, one pip per beat of the window), a switch
 * between the transcript and the X-ray, and one pane holding whichever is chosen.
 *
 * Nothing here decides what a viewer may see. The transcript's lines are the drawer's own
 * (`drawerLines`), so the vote's result and the lynch's line wait exactly as long as they do
 * in the drawer; the X-ray pane is the stage's own film, drawn by a small stage of its own
 * that shows only the film's corner. The replay theatre holds the state and hands it here.
 */
import { useLayoutEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import type { Character } from '@/assets/manifest';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import type { MiniUnder } from '@/stage/containers/ReplayTheatre';
import {
  ACT_VERB,
  DEFAULT_FILTERS,
  WINNER_TEXT,
  drawerLines,
  filterLines,
  litKey,
  type DrawerLine,
} from '@/stage/drawer/drawer-lines';
import { Film } from '@/stage/film/Film';
import { ROLE_NAME, factionOf, seatNumber, seatify } from '@/stage/roles';
import { Stage } from '@/stage/Stage';
import { STAGE_W, sideSlot } from '@/stage/units';
import classes from './CarriageUnder.module.css';

const PASS_REASON: Record<string, string> = {
  voluntary: 'chose to pass',
  novelty_gated: 'held back: nothing new to say',
  generation_failed: 'no line came',
};

export function CarriageUnder(u: MiniUnder) {
  const film = u.pane === 'film';
  return (
    <div className={classes.under}>
      <div className={classes.bar}>
        <button
          type="button"
          className={classes.play}
          aria-label={u.playing ? 'Pause' : 'Play'}
          aria-pressed={u.playing}
          onClick={u.onTogglePlay}
        >
          <svg viewBox="0 0 16 16" aria-hidden="true">
            <path d={u.playing ? 'M4 3h3v10H4zm5 0h3v10H9z' : 'M5 3l9 5-9 5z'} />
          </svg>
        </button>
        {/* the beat's own name: the marquee already says which day and vote this is */}
        <span className={classes.label} title={u.label}>
          {u.beat.label}
        </span>
        <span className={classes.pips} role="group" aria-label="Beats">
          {u.beats.map((b, i) => (
            <button
              key={i}
              type="button"
              aria-label={b.label}
              aria-current={i === u.index ? 'step' : undefined}
              className={i < u.index ? classes.done : undefined}
              onClick={() => u.onSeek(i)}
            />
          ))}
        </span>
      </div>
      <div className={classes.switch} role="group" aria-label="Under the stage">
        <button type="button" aria-pressed={!film} onClick={u.onTranscript}>
          Transcript
        </button>
        <button type="button" className={classes.xr} aria-pressed={film} onClick={u.onXray}>
          X-ray
        </button>
      </div>
      {film ? <FilmPane {...u} /> : <Transcript {...u} />}
    </div>
  );
}

/**
 * The film is drawn in stage units, beside a 1600-unit stage. A stage of its own, scaled so
 * the film's box fills the pane's width, shows only that corner: the same film, at a size a
 * phone can read (the stage's legibility floor grows its type below three-quarter scale).
 */
function FilmPane({ view, beat, ahead, cast, filmTab, onFilmTab }: MiniUnder) {
  const box = useRef<HTMLDivElement>(null);
  const [w, setW] = useState(0);
  useLayoutEffect(() => {
    const el = box.current;
    if (!el) return;
    setW(el.getBoundingClientRect().width);
    const ro = new ResizeObserver(([e]) => setW(e.contentRect.width));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  const r = sideSlot('replay');
  const m = 24; // room for the film's tilt and its shadow
  const k = w / (r.w + 2 * m);
  return (
    <div
      ref={box}
      className={classes.filmPane}
      style={{ height: (r.h + 2 * m) * k || undefined }}
    >
      {w ? (
        <div
          className={classes.filmStage}
          style={{
            width: STAGE_W * k,
            marginLeft: -(r.x - m) * k,
            marginTop: -(r.y - m) * k,
          }}
        >
          <Stage
            hud={
              <Film
                view={view}
                beat={beat}
                hud="replay"
                cast={cast}
                ahead={ahead}
                tab={filmTab}
                onTab={onFilmTab}
              />
            }
          />
        </div>
      ) : null}
    </div>
  );
}

/** The day on stage, as the drawer lists it, the beat's own line lit and scrolled to. */
function Transcript({ view, beat, xray, cast, index }: MiniUnder) {
  const lines = useMemo(
    () => drawerLines(view, { me: null, xray, beat }),
    [view, xray, beat],
  );
  const shown = useMemo(
    () => filterLines(lines, { ...DEFAULT_FILTERS, day: beat.day }),
    [lines, beat.day],
  );
  const lit = litKey(lines, beat);
  const scroller = useRef<HTMLDivElement>(null);
  useLayoutEffect(() => {
    const el = scroller.current;
    if (!el) return;
    const now = lit ? el.querySelector<HTMLElement>(`[data-line="${lit}"]`) : null;
    el.scrollTo({
      top: now ? Math.max(0, now.offsetTop - el.clientHeight * 0.4) : el.scrollHeight,
    });
  }, [lit, shown, index]);

  const chip = (seat: string) => <Chip seat={seat} cast={cast} />;
  const role = (seat: string) => {
    const r = xray ? view.xray.roles[seat] : null;
    if (!r) return null;
    return (
      <span className={classes.role} data-faction={factionOf(r) ?? undefined}>
        {(ROLE_NAME[r] ?? r).toLowerCase()}
      </span>
    );
  };
  return (
    <div
      ref={scroller}
      className={classes.lines}
      aria-label={xray ? 'Transcript, with the X-ray’s lines' : 'Transcript'}
    >
      {shown.length ? (
        shown.map((l) => (
          <Line key={l.key} line={l} lit={l.key === lit} chip={chip} role={role} />
        ))
      ) : (
        <p className={classes.empty}>Nothing said yet today.</p>
      )}
    </div>
  );
}

function Chip({ seat, cast }: { seat: string; cast: readonly Character[] }) {
  const c = seat ? cast[seatNumber(seat) - 1] : undefined;
  return <span className={classes.chip}>{c ? <ChipSprite character={c} /> : null}</span>;
}

function Line({
  line: l,
  lit,
  chip,
  role,
}: {
  line: DrawerLine;
  lit: boolean;
  chip: (seat: string) => ReactNode;
  role: (seat: string) => ReactNode;
}) {
  const row = (tier: 'public' | 'xray', who: ReactNode, text?: ReactNode, seat = '') => (
    <div
      className={classes.line}
      data-line={l.key}
      data-tier={tier}
      data-lit={lit || undefined}
    >
      {chip(seat)}
      <div className={classes.who}>{who}</div>
      {text ? <div className={classes.txt}>{text}</div> : null}
    </div>
  );
  switch (l.kind) {
    case 'rule':
      return (
        <div className={classes.rule} data-line={l.key}>
          {l.text}
        </div>
      );
    case 'speech':
      return row(
        'public',
        <>
          Seat {seatNumber(l.player)}
          {role(l.player)}
        </>,
        seatify(l.text),
        l.player,
      );
    case 'pass':
      return row(
        'xray',
        <>
          Seat {seatNumber(l.player)} passes{role(l.player)}{' '}
          <i>{l.reason ? (PASS_REASON[l.reason] ?? l.reason) : 'chose to pass'}</i>
        </>,
        l.draft ? <s>{seatify(l.draft)}</s> : null,
        l.player,
      );
    case 'gm':
      return row('public', 'The table', seatify(l.text));
    case 'votes':
      return row(
        'public',
        `The table votes, ${l.pairs.length} ballot${l.pairs.length === 1 ? '' : 's'} at the count`,
        <span className={classes.pairs}>
          {l.pairs.map((p) => (
            <span key={p.voter}>
              {seatNumber(p.voter)} → {p.votee === 'abstain' ? '·' : seatNumber(p.votee)}
            </span>
          ))}
        </span>,
      );
    case 'act':
      return row(
        'xray',
        <>
          Seat {seatNumber(l.actor)} {ACT_VERB[l.role] ?? 'acts on'} seat{' '}
          {seatNumber(l.target)}
          {role(l.actor)}
        </>,
        undefined,
        l.actor,
      );
    case 'pack':
      return row(
        'xray',
        <>
          Pack · Seat {seatNumber(l.wolf)} <i>round {l.round}</i>
        </>,
        seatify(l.text),
        l.wolf,
      );
    case 'kill':
      return row('xray', `The pack chooses seat ${seatNumber(l.target)}`);
    case 'only':
      return row(
        'xray',
        <>
          {l.who} <i>{l.about}</i>
        </>,
        typeof l.text === 'string' ? seatify(l.text) : `${l.text.lead}${l.text.rest}`, // the chip is a picture beside words that name the seat
      );
    case 'brief':
      return row('xray', `The day’s brief, day ${l.day}`, seatify(l.text));
    case 'over':
      return row('public', WINNER_TEXT[l.winner] ?? l.winner);
  }
}
