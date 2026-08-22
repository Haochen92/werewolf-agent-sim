'use client';

/**
 * The theater's chrome — scrubber, roster rail, X-ray toggle, agent inspector, vote matrix,
 * ghost guesses. Presentational throughout: each takes `GameView` slices and returns markup.
 */
import { useMemo, useState } from 'react';
import type { DayView, DeathRecord, GameView } from '@/game/types';
import type { Winner } from '@/types/contracts';
import { humanise } from '@/lib/format';
import { SeatChip } from './SeatChip';
import { PrivateResultCard } from './transcript-parts';
import classes from './Theater.module.css';

// --- winner chip -------------------------------------------------------------

const FACTION_CLASS: Record<Winner, string> = {
  villagers: classes.villagers,
  wolves: classes.wolves,
  serial_killer: classes.serialKiller,
};

const FACTION_LABEL: Record<Winner, string> = {
  villagers: 'Villagers win',
  wolves: 'Wolves win',
  serial_killer: 'Serial killer wins',
};

export function WinnerChip({ winner }: { winner: Winner }) {
  return (
    <span className={`${classes.winnerChip} ${FACTION_CLASS[winner]}`}>
      {FACTION_LABEL[winner]}
    </span>
  );
}

// --- X-ray toggle ------------------------------------------------------------

export function XrayToggle({
  on,
  available,
  showHint,
  onToggle,
}: {
  on: boolean;
  available: boolean;
  showHint?: boolean;
  onToggle: () => void;
}) {
  return (
    <>
      <button
        type="button"
        className={`${classes.xrayToggle} ${on ? classes.xrayOn : ''}`}
        onClick={onToggle}
        disabled={!available}
        aria-pressed={on}
        title={
          available
            ? 'Roles, scheduler reasons, the wolf channel, and the speeches that were vetoed'
            : 'This log carries no observer-tier data'
        }
      >
        <span className={classes.xrayDot} aria-hidden="true" />
        X-ray {on ? 'on' : 'off'}
      </button>
      {showHint && available && !on ? (
        <span className={classes.hint}>see what everyone was really thinking</span>
      ) : null}
    </>
  );
}

// --- scrubber ----------------------------------------------------------------

/**
 * Day/phase stepper. v1 is step-through, NOT autoplay — staged-pacing autoplay is parked
 * polish (ux_baseline §6). Steps come from the phases that actually happened, which is why
 * day 1 of the seeded game shows two steps and every later day shows three.
 */
export function DayScrubber({
  days,
  current,
  onSelect,
}: {
  days: DayView[];
  current: number;
  onSelect: (day: number) => void;
}) {
  const index = days.findIndex((d) => d.day === current);
  return (
    <div className={classes.scrubber}>
      <button
        type="button"
        className={classes.arrowButton}
        onClick={() => onSelect(days[index - 1].day)}
        disabled={index <= 0}
        aria-label="Previous day"
      >
        ←
      </button>
      {days.map((day) => (
        <button
          key={day.day}
          type="button"
          className={`${classes.step} ${day.day === current ? classes.stepActive : ''}`}
          onClick={() => onSelect(day.day)}
          aria-current={day.day === current}
        >
          Day {day.day}
          {day.phases.includes('night') ? ' ☾' : ''}
        </button>
      ))}
      <button
        type="button"
        className={classes.arrowButton}
        onClick={() => onSelect(days[index + 1].day)}
        disabled={index < 0 || index >= days.length - 1}
        aria-label="Next day"
      >
        →
      </button>
    </div>
  );
}

// --- roster ------------------------------------------------------------------

export function RosterRail({
  view,
  xray,
  upToDay,
  onInspect,
}: {
  view: GameView;
  xray: boolean;
  /** Deaths after this day are not yet known to the reader at this scrubber position. */
  upToDay: number;
  onInspect?: (seat: string) => void;
}) {
  const deadByDay = useMemo(() => {
    const map = new Map<string, DeathRecord>();
    for (const death of view.dead) if (death.day <= upToDay) map.set(death.player, death);
    return map;
  }, [view.dead, upToDay]);

  return (
    <div>
      <div className={classes.railHead}>
        The table · {view.seats.length - deadByDay.size}/{view.seats.length} alive
      </div>
      <div className={classes.rosterStrip}>
        {view.seats.map((seat) => (
          <SeatChip
            key={seat}
            seat={seat}
            role={xray ? view.xray.roles[seat] : undefined}
            dead={deadByDay.has(seat)}
            isSelf={seat === view.me.seat}
            onClick={onInspect ? () => onInspect(seat) : undefined}
          />
        ))}
      </div>
    </div>
  );
}

// --- agent inspector ---------------------------------------------------------

/**
 * The machine world proper: what one agent was thinking, in order. Opened by clicking any
 * seat while the X-ray is on. Its strategy timeline is the clearest single artefact of the
 * agent's reasoning the wire carries.
 */
export function AgentInspector({
  seat,
  view,
  onClose,
}: {
  seat: string;
  view: GameView;
  onClose: () => void;
}) {
  const agent = view.xray.agents[seat];
  const role = view.xray.roles[seat];
  const death = view.dead.find((d) => d.player === seat);
  const privateResults = view.xray.privateResults[seat] ?? [];

  const nightActions = useMemo(
    () =>
      Object.values(view.days)
        .flatMap((day) =>
          day.night ? day.night.actions.map((a) => ({ ...a, day: day.day })) : [],
        )
        .filter((action) => action.actor === seat),
    [view.days, seat],
  );

  return (
    <div className={classes.machinePanel}>
      <div className={classes.panelHead}>
        {seat}
        <button
          type="button"
          className={classes.closeButton}
          onClick={onClose}
          aria-label="Close"
        >
          ✕
        </button>
      </div>
      <div style={{ marginBottom: 'var(--space-3)' }}>
        role: {role ? humanise(role) : 'unknown'}
        {death ? ` · died day ${death.day} (${death.causes.join('+')})` : ' · survived'}
      </div>

      {nightActions.length > 0 ? (
        <>
          <div className={classes.panelHead}>night actions</div>
          <div style={{ marginBottom: 'var(--space-3)' }}>
            {nightActions.map((action) => (
              <div key={action.seq}>
                n{action.day}: → {action.target}
              </div>
            ))}
          </div>
        </>
      ) : null}

      {privateResults.length > 0 ? (
        <>
          <div className={classes.panelHead}>private results</div>
          <div
            style={{
              display: 'grid',
              gap: 'var(--space-2)',
              marginBottom: 'var(--space-3)',
            }}
          >
            {privateResults.map((result) => (
              <PrivateResultCard key={result.seq} result={result} />
            ))}
          </div>
        </>
      ) : null}

      <div className={classes.panelHead}>strategy timeline</div>
      {!agent || agent.strategy.length === 0 ? (
        <div>no strategy recorded</div>
      ) : (
        agent.strategy.map((entry) => (
          <div key={entry.seq} className={classes.strategyEntry}>
            <span className={classes.strategyDay}>day {entry.day}</span>
            {entry.text}
          </div>
        ))
      )}
    </div>
  );
}

// --- vote matrix -------------------------------------------------------------

export function VoteMatrix({ view, day }: { view: GameView; day: DayView }) {
  const ballots = day.vote.ballots;
  if (ballots.length === 0) return null;

  const voters = view.seats.filter((seat) => ballots.some((b) => b.voter === seat));
  const targets = [...new Set(ballots.map((b) => b.votee))];
  const cast = new Map(ballots.map((b) => [b.voter, b.votee]));

  return (
    <div className={classes.machinePanel}>
      <div className={classes.panelHead}>vote matrix · day {day.day}</div>
      <div className={classes.matrixScroll}>
        <table className={classes.matrix}>
          <thead>
            <tr>
              <th />
              {targets.map((target) => (
                <th key={target}>{target.replace('player_', 'p')}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {voters.map((voter) => (
              <tr key={voter}>
                <td className={classes.matrixVoter}>{voter.replace('player_', 'p')}</td>
                {targets.map((target) => (
                  <td
                    key={target}
                    className={cast.get(voter) === target ? classes.matrixHit : ''}
                  >
                    {cast.get(voter) === target ? '●' : '·'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- ghost guesses (localStorage, ruling 7) ----------------------------------

/**
 * "Who do you suspect?" at each day boundary, kept in localStorage and scored against the
 * truth at the end. Skippable and never blocking — it is a side game, and a reader who
 * ignores it should never notice it is there.
 */
export function GhostGuess({
  day,
  seats,
  deadSeats,
  guess,
  truth,
  revealed,
  onGuess,
}: {
  day: number;
  seats: string[];
  deadSeats: Set<string>;
  guess: string | undefined;
  /** The real role of the guessed seat — only once the game is over. */
  truth: Record<string, string>;
  revealed: boolean;
  onGuess: (seat: string) => void;
}) {
  const alive = seats.filter((seat) => !deadSeats.has(seat));
  const verdict =
    revealed && guess
      ? truth[guess] === 'wolf'
        ? 'right'
        : `no — ${truth[guess] ?? '?'}`
      : null;

  return (
    <div className={classes.ghost}>
      <div className={classes.ghostHead}>Day {day} · who is a wolf?</div>
      <div className={classes.ghostOptions}>
        {alive.map((seat) => (
          <button
            key={seat}
            type="button"
            className={`${classes.ghostOption} ${guess === seat ? classes.ghostPicked : ''}`}
            onClick={() => onGuess(seat)}
          >
            {seat.replace('player_', 'p')}
          </button>
        ))}
      </div>
      {verdict ? (
        <div
          className={`${classes.ghostVerdict} ${
            verdict === 'right' ? classes.ghostRight : classes.ghostWrong
          }`}
        >
          you guessed {guess}: {verdict === 'right' ? 'a wolf. good read.' : verdict}
        </div>
      ) : null}
    </div>
  );
}

// --- small helper used by the theater ---------------------------------------

export function useToggle(initial = false): [boolean, () => void] {
  const [value, setValue] = useState(initial);
  return [value, () => setValue((v) => !v)];
}

export { classes as theaterClasses };
