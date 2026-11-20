'use client';

/**
 * The seated player's own file on a seat, in the case file (owner, 2026-10-18: the notes moved
 * here from a card over the stage; picks over writing). A tap on a seat's photo on the rail
 * opens it, and the folder's seat tabs page through them.
 *
 * The cover holds what stands for the whole game: the role the seat claims and, stamped on in
 * the side's ink, the role the player thinks it holds ("I think they are…"; on a seat that is
 * out, the role its death showed). Beside the claim, the morning's Record says whether the
 * table has it the same. On the player's own seat the claim is their cover, and the stamp the
 * role they hold.
 *
 * Then a tab per day, added as the days come. A day's page: what the seat said it did the night
 * before, picked rather than written (the claimed role sets the verb, `CLAIM_FORM`; the seats are
 * faces to pick), the Record's line for that night under it; the day's vote, filled in from the
 * table; and the player's own lines. Labels are the file's typewriter, the player's answers a
 * pencil hand. It is kept on this device (notebook.ts).
 */
import { useEffect, useRef, useState, type ReactNode } from 'react';
import type { GameView } from '@/game/types';
import type { LedgerDay } from '@/types/contracts';
import { Sigil } from '../instruments/Sigil';
import { CLAIM_FORM, guessChoices, type NightClaim, type Notebook } from '../notebook';
import { factionOf, ROLE_NAME, ROLE_ORDER, seatify, seatNumber } from '../roles';
import { claimedActionText } from './record-model';
import film from './Film.module.css';
import styles from './PlayerFile.module.css';

export interface PlayerFileProps {
  seat: string;
  /** The viewer's own seat. */
  me: string;
  view: GameView;
  book: Notebook;
  /**
   * The roles the game deals, with how many (`view.castRoleCounts`): a claim may name any; a
   * guess only one that could still be alive (`guessChoices`).
   */
  cast: Readonly<Record<string, number>>;
  /** The day the stage is on: the file's last tab. */
  day: number;
  ledger: readonly LedgerDay[] | null;
  chip: (seat: string, cls?: string) => ReactNode;
  /** The cover's name: on a phone, the way to another file. */
  chooser: ReactNode;
}

const name = (role: string) => ROLE_NAME[role] ?? role;

export function PlayerFile({
  seat,
  me,
  view,
  book,
  cast,
  day,
  ledger,
  chip,
  chooser,
}: PlayerFileProps) {
  const n = seatNumber(seat);
  const own = seat === me;
  const dead = view.dead.find((d) => d.player === seat);
  const [open, setOpen] = useState(Math.max(1, day));
  const shown = Math.min(open, Math.max(1, day));
  const claim = book.claims[n];
  const guess = book.guesses[n];
  // the morning's Record: the role the seat claims there, if any, and its claimed nights
  const record = ledger?.at(-1)?.players.find((p) => p.player === seat);
  const recordRole = record?.roles.filter((r) => r.kind === 'claimed').at(-1)?.role;
  const truth = own ? view.me.role?.role : dead?.role;
  const roles = Object.keys(cast);
  const living = guessChoices(
    cast,
    view.dead.map((d) => d.role),
  ).map((c) => c.role);
  return (
    <>
      <div className={film.head}>
        <div className={`${film.cover} ${styles.cover}`} data-player-file={n}>
          {chip(seat)}
          <div className={`${film.who} ${styles.who}`}>
            <span className={film.nameRow}>{chooser}</span>
            <span className={styles.claim}>
              <span className={styles.label}>{own ? 'I claim' : 'Claims'}</span>
              <RoleField
                value={claim}
                roles={roles}
                none={own ? 'No claim yet' : 'No claim'}
                label={own ? 'The role you claim' : `The role seat ${n} claims`}
                onPick={(r) => book.setClaim(n, r)}
              />
              {recordRole ? (
                <span className={styles.recordRole} data-record-role={recordRole}>
                  {recordRole === claim ? '✓ on the record' : `record: ${name(recordRole)}`}
                </span>
              ) : null}
            </span>
          </div>
          {truth ? (
            <span className={styles.guess}>
              <span className={styles.label}>{own ? 'You are' : 'Was'}</span>
              <RoleStamp role={truth} />
            </span>
          ) : own || dead ? null : (
            <RoleField
              value={guess}
              roles={guess && !living.includes(guess) ? [...living, guess] : living}
              none="Not sure"
              label={`I think seat ${n} is`}
              onPick={(r) => book.setGuess(n, r)}
              stamp
            />
          )}
        </div>
        <div className={film.dividers} role="tablist" aria-label="Days">
          {Array.from({ length: Math.max(1, day) }, (_, i) => i + 1).map((d) => (
            <button
              key={d}
              type="button"
              role="tab"
              className={film.tab}
              aria-selected={d === shown}
              onClick={() => setOpen(d)}
            >
              Day {d}
            </button>
          ))}
        </div>
      </div>
      <div key={shown} className={film.sheet} role="tabpanel" data-day-page={shown}>
        <div className={film.shHead}>
          <span className={film.title}>Day {shown}</span>
          <span className={film.typed}>kept on this device</span>
        </div>
        {shown > 1 ? (
          <Night
            n={shown - 1}
            own={own}
            claim={claim}
            value={book.nights[n]?.[shown - 1]}
            seats={view.seats}
            chip={chip}
            onChange={(c) => book.setNight(n, shown - 1, c)}
            record={record?.entries.filter((e) => e.night === shown - 1) ?? []}
          />
        ) : null}
        <Vote view={view} seat={seat} day={shown} past={shown < day} own={own} chip={chip} />
        <p className={film.sect}>{own ? 'My lines' : 'Your lines'}</p>
        <textarea
          className={styles.lines}
          value={book.lines[n]?.[shown] ?? ''}
          placeholder="+ a line"
          aria-label={`Your lines on seat ${n}, day ${shown}`}
          rows={3}
          onChange={(e) => book.setLine(n, shown, e.target.value)}
        />
      </div>
    </>
  );
}

/** A role stamped on in its side's ink, its sigil in the ink too. */
function RoleStamp({ role }: { role: string }) {
  const f = factionOf(role);
  return (
    <span className={`${film.stamp} ${f ? film[`s-${f}`] : ''} ${styles.stamp}`}>
      <Sigil role={role} width={20} height={20} />
      {name(role)}
    </span>
  );
}

/**
 * A role to pick: the claim (pencilled on a dotted blank) or the guess (a stamp, a dashed blank
 * while not sure), opening a card of the game's roles by side, each with its sigil.
 */
function RoleField({
  value,
  roles,
  none,
  label,
  onPick,
  stamp = false,
}: {
  value: string | undefined;
  roles: readonly string[];
  none: string;
  label: string;
  onPick: (role: string | null) => void;
  stamp?: boolean;
}) {
  const [open, setOpen, box] = usePop<HTMLSpanElement>();
  const pick = (r: string | null) => {
    setOpen(false);
    onPick(r);
  };
  const order = [...ROLE_ORDER.filter((r) => roles.includes(r)), ...roles.filter((r) => !ROLE_ORDER.includes(r))];
  const sides: [string, string[]][] = [
    ['Town', order.filter((r) => factionOf(r) === 'villagers')],
    ['Wolves', order.filter((r) => factionOf(r) === 'wolves')],
    ['On their own', order.filter((r) => !['villagers', 'wolves'].includes(factionOf(r) ?? ''))],
  ];
  return (
    <span ref={box} className={stamp ? styles.guess : styles.pop}>
      {stamp ? <span className={styles.label}>I think they are</span> : null}
      <button
        type="button"
        className={stamp ? styles.stampButton : styles.field}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={`${label}: ${value ? name(value) : none}`}
        onClick={() => setOpen((o) => !o)}
      >
        {stamp ? (
          value ? (
            <RoleStamp role={value} />
          ) : (
            <span className={`${film.stamp} ${styles.blankStamp}`}>{none}</span>
          )
        ) : (
          <>
            {value ? <Sigil role={value} variant="felt" width={18} height={18} /> : null}
            {value ? name(value) : <span className={styles.unset}>{none}</span>}
            <i className={styles.caret} aria-hidden="true">
              ▾
            </i>
          </>
        )}
      </button>
      {open ? (
        <span className={styles.roles} role="dialog" aria-label={label}>
          <button
            type="button"
            className={`${styles.role} ${styles.unsure}`}
            aria-pressed={!value}
            onClick={() => pick(null)}
          >
            {none}
          </button>
          {sides.map(([side, list]) =>
            list.length ? (
              <span key={side} className={styles.side}>
                <span className={styles.label}>{side}</span>
                {list.map((r) => (
                  <button
                    key={r}
                    type="button"
                    className={styles.role}
                    aria-pressed={r === value}
                    onClick={() => pick(r)}
                  >
                    <Sigil role={r} variant="felt" width={22} height={22} />
                    {name(r)}
                  </button>
                ))}
              </span>
            ) : null,
          )}
        </span>
      ) : null}
    </span>
  );
}

/** What the seat said it did the night before this day, as the claimed role does it. */
function Night({
  n,
  own,
  claim,
  value = {},
  seats,
  chip,
  onChange,
  record,
}: {
  n: number;
  own: boolean;
  claim: string | undefined;
  value?: NightClaim;
  seats: readonly string[];
  chip: (seat: string, cls?: string) => ReactNode;
  onChange: (c: NightClaim | null) => void;
  record: readonly { night: number; action: string; target: string; result: string }[];
}) {
  const form = claim ? CLAIM_FORM[claim] : undefined;
  const set = (c: Partial<NightClaim>) => onChange({ ...value, ...c });
  return (
    <>
      <p className={film.sect}>
        Night {n} · {own ? 'what I said' : 'their claim'}
      </p>
      {!claim ? (
        <p className={film.none}>
          {own ? 'Pick the role you claim above' : 'Pick their claim above'} to note the night.
        </p>
      ) : !form ? (
        <p className={film.none}>A {name(claim).toLowerCase()} has no night to note.</p>
      ) : form.from && n < form.from ? (
        <p className={film.none}>
          A {name(claim).toLowerCase()} does not act on night {n}.
        </p>
      ) : (
        <>
          <div className={styles.row}>
            <span>{form.verb}</span>
            <SeatField
              seats={seats}
              picked={value.target ? [value.target] : []}
              chip={chip}
              label={`Night ${n}: ${form.verb}`}
              onPick={(s) => set({ target: s[0] })}
            />
          </div>
          {form.seen ? (
            <div className={styles.row}>
              <span>{form.seen}</span>
              <SeatField
                seats={seats}
                picked={value.seen ?? []}
                none={!!value.none}
                chip={chip}
                label={`Night ${n}: ${form.seen}`}
                many
                onPick={(s, none) => set({ seen: s, none })}
              />
            </div>
          ) : null}
          {form.results ? (
            <div className={styles.row}>
              {form.results.map((r) => (
                <button
                  key={r.id}
                  type="button"
                  className={styles.chipButton}
                  aria-pressed={value.result === r.id}
                  onClick={() => set({ result: value.result === r.id ? undefined : r.id })}
                >
                  {r.words}
                </button>
              ))}
            </div>
          ) : null}
        </>
      )}
      {record.map((e, i) => (
        <p key={i} className={styles.recordLine} data-record-night={e.night}>
          On the record: {seatify(claimedActionText(e).replace(/^Night \d+: /, ''))}
        </p>
      ))}
    </>
  );
}

/**
 * Seats picked as faces on pencilled chips. One (`many` unset) or several, and for several "no
 * one" as well: a card of every seat's face opens from the chip, or from "+ seat".
 */
function SeatField({
  seats,
  picked,
  none = false,
  chip,
  label,
  many = false,
  onPick,
}: {
  seats: readonly string[];
  picked: readonly number[];
  none?: boolean;
  chip: (seat: string, cls?: string) => ReactNode;
  label: string;
  many?: boolean;
  onPick: (seats: number[], none?: boolean) => void;
}) {
  const [open, setOpen, box] = usePop<HTMLSpanElement>();
  const toggle = (s: number) => {
    if (!many) {
      setOpen(false);
      onPick(picked[0] === s ? [] : [s]);
      return;
    }
    onPick(picked.includes(s) ? picked.filter((x) => x !== s) : [...picked, s], false);
  };
  const face = (s: number) => chip(`player_${s}`, styles.face);
  return (
    <span ref={box} className={styles.pop}>
      {none ? (
        <button type="button" className={styles.seat} onClick={() => setOpen((o) => !o)}>
          no one
          <i className={styles.caret} aria-hidden="true">
            ▾
          </i>
        </button>
      ) : (
        picked.map((s) => (
          <button
            key={s}
            type="button"
            className={styles.seat}
            aria-label={`${label}: seat ${s}`}
            onClick={() => setOpen((o) => !o)}
          >
            {face(s)}
            Seat {s}
            <i className={styles.caret} aria-hidden="true">
              ▾
            </i>
          </button>
        ))
      )}
      {(!picked.length && !none) || (many && !none) ? (
        <button
          type="button"
          className={styles.add}
          aria-haspopup="dialog"
          aria-expanded={open}
          aria-label={`${label}: pick a seat`}
          onClick={() => setOpen((o) => !o)}
        >
          + seat
        </button>
      ) : null}
      {open ? (
        <span className={styles.seats} role="dialog" aria-label={label}>
          {seats.map((s) => {
            const k = seatNumber(s);
            return (
              <button
                key={s}
                type="button"
                className={film.pick}
                aria-pressed={picked.includes(k)}
                onClick={() => toggle(k)}
              >
                {chip(s)}
                {k}
              </button>
            );
          })}
          {many ? (
            <>
              <button
                type="button"
                className={`${film.pick} ${styles.wide}`}
                aria-pressed={none}
                onClick={() => {
                  setOpen(false);
                  onPick([], !none);
                }}
              >
                No one
              </button>
              <button
                type="button"
                className={`${film.pick} ${styles.wide}`}
                onClick={() => setOpen(false)}
              >
                Done
              </button>
            </>
          ) : null}
        </span>
      ) : null}
    </span>
  );
}

/** The day's vote as the table cast it: the seat's ballot and the ballots on it. */
function Vote({
  view,
  seat,
  day,
  past,
  own,
  chip,
}: {
  view: GameView;
  seat: string;
  day: number;
  /** The day is behind the stage: its vote is over, or there was none. */
  past: boolean;
  own: boolean;
  chip: (seat: string, cls?: string) => ReactNode;
}) {
  const ballots = view.days[day]?.vote.ballots ?? [];
  const cast = ballots.find((b) => b.voter === seat);
  const on = ballots.filter((b) => b.votee === seat);
  const face = (s: string) => chip(s, styles.face);
  return (
    <>
      <div className={styles.sectRow}>
        <p className={film.sect}>The vote · day {day}</p>
        <span className={styles.from}>from the table</span>
      </div>
      {!ballots.length ? (
        <p className={film.none}>
          {past || view.days[day]?.vote.outcome
            ? 'No votes were cast that day.'
            : 'Filled in when the votes are cast.'}
        </p>
      ) : (
        <>
          <p className={styles.auto} data-vote-cast>
            {cast ? (
              <>
                {own ? 'I voted for' : 'Voted for'} {face(cast.votee)}
                <b>Seat {seatNumber(cast.votee)}</b>
              </>
            ) : (
              <>{own ? 'I cast no ballot' : 'Cast no ballot'}</>
            )}
          </p>
          <p className={styles.auto} data-vote-on>
            {on.length ? (
              <>
                {on.map((b) => (
                  <span key={b.voter}>{face(b.voter)}</span>
                ))}
                {own ? 'voted for me: ' : 'voted for them: '}
                <b>{on.map((b) => `Seat ${seatNumber(b.voter)}`).join(', ')}</b>
              </>
            ) : (
              <>{own ? 'No one voted for me' : 'No one voted for them'}</>
            )}
          </p>
        </>
      )}
    </>
  );
}

/** A small card's open state, closed by a press outside it or Escape. */
function usePop<T extends HTMLElement>() {
  const [open, setOpen] = useState(false);
  const box = useRef<T>(null);
  useEffect(() => {
    if (!open) return;
    const away = (e: PointerEvent) => {
      if (!box.current?.contains(e.target as Node)) setOpen(false);
    };
    const esc = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false);
    document.addEventListener('pointerdown', away);
    document.addEventListener('keydown', esc);
    return () => {
      document.removeEventListener('pointerdown', away);
      document.removeEventListener('keydown', esc);
    };
  }, [open]);
  return [open, setOpen, box] as const;
}
