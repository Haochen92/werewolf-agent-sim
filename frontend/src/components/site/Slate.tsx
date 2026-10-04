/**
 * One finished game as a clapperboard slate (the landing and replays mockups' `.game/.slate`),
 * linking into the theatre at `/replays/[id]`. The winning side colours the frame and inks the
 * paper; the header says who won, and the printed line under it is stamped for human seats, memory
 * and "you played" (or, with nothing to stamp, prints the table's default); the
 * puppets are the game's own cast, one per seat (the same hash the theatre uses); the fields are the
 * record id, the days, the phase it ended in, and the model, with what the game cost and how long
 * an AI call took on average when the server recorded them (games from 2026-10-04 on).
 *
 * Pure: the page passes the model's display name (from `GET /models`) and whether this browser
 * sat in the game, so the slate itself never fetches.
 */
import Link from 'next/link';
import type { ReplaySummary, Winner } from '@/types/contracts';
import { castForGame } from '@/stage/cast/castForGame';
import { ChipSprite } from '@/stage/cast/ChipSprite';
import { Sigil } from '@/stage/instruments/Sigil';
import { endedLabel, formatCallSeconds, formatCost, formatDate } from '@/lib/format';
import classes from './Slate.module.css';

/** Seats at the table: the public casting's total (every archived game so far dealt nine). */
const seatCount = (r: ReplaySummary) =>
  Object.values(r.cast_role_counts).reduce((a, b) => a + b, 0) || undefined;

const NUMBER_WORDS = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine'];
const numberWord = (n: number) => NUMBER_WORDS[n] ?? String(n);

/**
 * The pre-printed table line for a game that departs from nothing: all agents, memory off. A
 * clapperboard's fields are printed and the stamps are for exceptions, so the row under the
 * verdict always carries one line — this when there is nothing to stamp — and every slate
 * stands the same height.
 */
const baselineLine = (r: ReplaySummary) => {
  const seats = seatCount(r);
  return `${seats ? `${numberWord(seats)} agents` : 'All agents'} · memory off`;
};

const FACTION: Record<
  Winner,
  { name: string; verb: string; sigil: string; className: string }
> = {
  villagers: { name: 'Villagers', verb: 'win', sigil: 'villager', className: classes.town },
  wolves: { name: 'Wolves', verb: 'win', sigil: 'wolf', className: classes.wolf },
  serial_killer: {
    name: 'Serial killer',
    verb: 'wins',
    sigil: 'serial_killer',
    className: classes.sk,
  },
};

export interface SlateProps {
  replay: ReplaySummary;
  /** The model's display name; the raw id is shown when the menu does not know it. */
  modelLabel?: string;
  /** This browser holds a seat token for the game. */
  mine?: boolean;
  /** Where the slate sits, so the theatre's way out comes back to it (`?from=`, TheaterClient). */
  from?: 'home';
}

export function Slate({ replay, modelLabel, mine = false, from }: SlateProps) {
  const faction = FACTION[replay.winner];
  const ended = endedLabel(replay.ended_phase, replay.days);
  const date = formatDate(replay.finished_at);
  const model = replay.model ? (modelLabel ?? replay.model) : null;
  const cost = formatCost(replay.cost_usd);
  const callTime = formatCallSeconds(replay.avg_call_seconds);
  // Under the model's name: the game's cost and AI call time when recorded, then the date.
  const modelLine = [cost, callTime && `${callTime} per AI call`, date]
    .filter(Boolean)
    .join(' · ');
  const humans = replay.n_humans;

  const aria = [
    `Replay: ${faction.name.toLowerCase()} ${faction.verb}`,
    `${replay.days} ${replay.days === 1 ? 'day' : 'days'}`,
    ended ? `ended ${ended.toLowerCase()}` : null,
    model ?? 'model unrecorded',
    cost ? `cost ${cost}` : null,
    mine ? 'you played' : null,
  ]
    .filter(Boolean)
    .join(', ');

  return (
    <Link
      href={`/replays/${replay.game_id}${from ? `?from=${from}` : ''}`}
      className={`${classes.game} ${faction.className}`}
      aria-label={aria}
      data-game={replay.game_id}
    >
      <div className={classes.slate}>
        <div className={classes.band}>
          <span className={classes.plaque}>
            <span className={classes.dot}>
              <svg viewBox="0 0 24 24" aria-hidden="true">
                <path d="M5 3 L21 12 L5 21 Z" />
              </svg>
            </span>
            <span className={classes.plaqueText}>Replay</span>
          </span>
        </div>
        <div className={classes.in}>
          <div className={classes.watermark}>
            <Sigil role={faction.sigil} />
          </div>
          <div className={classes.hd}>
            <div className={classes.verdict}>
              {faction.name}
              <small>{faction.verb}</small>
            </div>
            {humans > 0 || replay.memory || mine ? (
              <div className={classes.stamps}>
                {humans > 0 ? (
                  <span className={classes.stamp}>
                    {humans === 1 ? 'One human' : `${numberWord(humans)} humans`} at the table
                  </span>
                ) : null}
                {replay.memory ? (
                  <span className={`${classes.stamp} ${classes.stampTilt}`}>Memory on</span>
                ) : null}
                {mine ? (
                  <span className={`${classes.stamp} ${classes.stampYou}`}>You played</span>
                ) : null}
              </div>
            ) : (
              <div className={classes.printed}>{baselineLine(replay)}</div>
            )}
          </div>
          <div className={classes.cast} aria-hidden="true">
            {castForGame(replay.game_id, seatCount(replay)).map((character, seat) => (
              <span key={seat} className={classes.chip}>
                <ChipSprite character={character} />
              </span>
            ))}
          </div>
          <dl className={classes.fields}>
            <div className={classes.f}>
              <dt>Record</dt>
              <dd>{replay.game_id.slice(0, 7).toUpperCase()}</dd>
            </div>
            <div className={classes.f}>
              <dt>Days</dt>
              <dd>{replay.days}</dd>
            </div>
            <div className={classes.f}>
              <dt>Ended</dt>
              <dd className={ended ? undefined : classes.none}>{ended ?? 'Unrecorded'}</dd>
            </div>
            <div className={`${classes.f} ${classes.wide}`}>
              <dt>Model</dt>
              {model ? (
                <dd>
                  {model}
                  {modelLine ? <span className={classes.mono}>{modelLine}</span> : null}
                </dd>
              ) : (
                <dd className={classes.none}>
                  Unrecorded
                  <span className={classes.mono}>
                    column added later{date ? ` · archived ${date}` : ''}
                  </span>
                </dd>
              )}
            </div>
          </dl>
        </div>
      </div>
    </Link>
  );
}

/** The slates' grid: two across, one on a narrow screen (the landing's `.games`). */
export function SlateGrid({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={className ? `${classes.grid} ${className}` : classes.grid}>
      {children}
    </div>
  );
}
