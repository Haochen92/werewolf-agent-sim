/**
 * One finished game as a clapperboard slate (the landing and replays mockups' `.game/.slate`),
 * linking into the theatre at `/replays/[id]`. The winning side colours the frame, inks the
 * paper and is watermarked on it as its badge; the header says who won, and the printed line
 * under it is stamped for human seats, memory and "you played" (or, with nothing to stamp,
 * prints the table's default); then the roles dealt, one disc per seat, town to neutral (a
 * neutral that won beside the winner is ringed); the fields are the record id, the phase it
 * ended in and the model, and under them what the game cost and how long an AI call took on
 * average when the server recorded them (games from 2026-10-04 on), then the date.
 *
 * Pure: the page passes the model's display name (from `GET /models`) and whether this browser
 * sat in the game, so the slate itself never fetches.
 */
import Link from 'next/link';
import type { ReplaySummary } from '@/types/contracts';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import {
  DRAW_NAME,
  ROLE_NAME,
  ROLE_ORDER,
  WINNER_NAME,
  factionOf,
  neutralWinner,
  winnerFaction,
  winnerKey,
  type WinnerKey,
} from '@/stage/roles';
import { endedLabel, formatCallSeconds, formatCost, formatDate } from '@/lib/format';
import classes from './Slate.module.css';

/** Seats at the table: the public casting's total (nine in the older games, ten since Phase 3). */
const seatCount = (r: ReplaySummary) =>
  Object.values(r.cast_role_counts).reduce((a, b) => a + b, 0) || undefined;

const NUMBER_WORDS = [
  '',
  'One',
  'Two',
  'Three',
  'Four',
  'Five',
  'Six',
  'Seven',
  'Eight',
  'Nine',
  'Ten',
];
const numberWord = (n: number) => NUMBER_WORDS[n] ?? String(n);

/** The roles dealt, one per seat, in the role sheet's order (town, the pack, lone killer, neutral). */
const rolesDealt = (r: ReplaySummary) =>
  ROLE_ORDER.flatMap((role) => Array<string>(r.cast_role_counts[role] ?? 0).fill(role));

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

/** A draw wears no side's colour and stamps no side's badge. */
const FACTION: Record<WinnerKey, { name: string; verb: string; className: string }> = {
  villagers: { name: WINNER_NAME.villagers, verb: 'wins', className: classes.town },
  wolves: { name: WINNER_NAME.wolves, verb: 'win', className: classes.wolf },
  serial_killer: { name: WINNER_NAME.serial_killer, verb: 'wins', className: classes.sk },
  necromancer: { name: WINNER_NAME.necromancer, verb: 'wins', className: classes.sk },
  draw: { name: DRAW_NAME, verb: '', className: classes.draw },
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
  const faction = FACTION[winnerKey(replay.winner)];
  const side = winnerFaction(replay.winner);
  const ended = endedLabel(replay.ended_phase, replay.days);
  const date = formatDate(replay.finished_at);
  const model = replay.model ? (modelLabel ?? replay.model) : null;
  const cost = formatCost(replay.cost_usd);
  const callTime = formatCallSeconds(replay.avg_call_seconds);
  const humans = replay.n_humans;
  const neutralWon = neutralWinner(replay.cast_role_counts, replay.neutral_result);

  const aria = [
    `Replay: ${faction.name.toLowerCase()} ${faction.verb}`.trim(),
    `${replay.days} ${replay.days === 1 ? 'day' : 'days'}`,
    ended ? `ended ${ended.toLowerCase()}` : null,
    neutralWon ? `the ${ROLE_NAME[neutralWon].toLowerCase()} won too` : null,
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
            {side ? (
              <FactionMark faction={side} format="badge" variant="stamp" small={false} />
            ) : null}
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
                    {humans === 1 ? 'One human' : `${numberWord(humans)} humans`} at the
                    table
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
            {rolesDealt(replay).map((role, seat) => (
              <span
                key={seat}
                className={classes.role}
                data-role={role}
                data-faction={factionOf(role) ?? undefined}
                data-won={role === neutralWon || undefined}
                title={`${ROLE_NAME[role] ?? role}${role === neutralWon ? ', won' : ''}`}
              >
                <Sigil role={role} small />
              </span>
            ))}
          </div>
          <dl className={classes.fields}>
            <div className={classes.f}>
              <dt>Record</dt>
              <dd>{replay.game_id.slice(0, 7).toUpperCase()}</dd>
            </div>
            <div className={classes.f}>
              <dt>Ended</dt>
              <dd className={ended ? undefined : classes.none}>{ended ?? 'Unrecorded'}</dd>
            </div>
            <div className={classes.f}>
              <dt>Model</dt>
              <dd className={model ? undefined : classes.none}>{model ?? 'Unrecorded'}</dd>
            </div>
            <div className={classes.run}>
              <div className={classes.figs}>
                <div className={classes.fig}>
                  <dt>Cost</dt>
                  <dd className={cost ? undefined : classes.none}>{cost || '—'}</dd>
                </div>
                <div className={classes.fig}>
                  <dt>Per AI call</dt>
                  <dd className={callTime ? undefined : classes.none}>{callTime || '—'}</dd>
                </div>
              </div>
              {date ? <span className={classes.mono}>{date}</span> : null}
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
