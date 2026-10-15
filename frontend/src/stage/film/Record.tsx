'use client';

/**
 * The Record: one morning's sheet in the case file (owner, 2026-10-04), what the agents read
 * that morning about the days before, set out the way the Reads sheet is. The data is
 * record-model.ts; the folder around it is Film.tsx.
 *
 * - Claims: a row per player who claimed, their face and seat and the role they claim now, in
 *   plain ink (a claim is not a fact, so never a faction's colour or a stamp), struck through
 *   when withdrawn; the role's history if it changed; then each claimed night action on a line
 *   ("Night 2 · investigated (face) Seat 9 → healer"), what it replaced struck through under it.
 *   Under each, the game's checks: ✓ in green where the record agrees, ✗ in rust where it
 *   disagrees or a rule is broken, a plain note otherwise. A plan the player announced is a
 *   graphite pencil note in the margin's hand, never the red pencil: a plan binds no one.
 * - Accusations of the day before: accusers' faces → the accused's, the reasoning two lines
 *   long until opened, "Defence ▸" for the defence and who disputed it, and where the
 *   accusation runs against the record, that ✗ line, always shown.
 *
 * - The night before the morning, in the engine's words: the viewer's own seat's night records
 *   (a ten-seat game), every seat's with the X-ray; the pack's kill once.
 *
 * A page is named by the day it records ("Day 2's record", read the morning of day 3), as the
 * transcript's pointer to it is. A pager turns back to earlier days, never past the stage's.
 * A game that ended at dawn ends on "Night 3's record": that night's records alone, no claims
 * or accusations (no morning read them).
 */
import { useState, type ReactNode } from 'react';
import type { SummaryAccusation } from '@/game/types';
import type { LedgerCheck, LedgerEntry, LedgerPlayer } from '@/types/contracts';
import { ROLE_NAME, seatNumber, seatify } from '../roles';
import {
  CLAIM_VERB,
  PLAN_VERB,
  currentClaim,
  nightName,
  planKind,
  resultWords,
  type NightRecordLine,
  type RecordPage,
} from './record-model';
import styles from './Film.module.css';

type Chip = (seat: string, cls?: string) => ReactNode;

export interface RecordSheetProps {
  /** The morning open; null before the first record (the end of day 1). */
  page: RecordPage | null;
  /** The mornings the stage has reached, oldest first: the pager's pages. */
  mornings: readonly number[];
  onMorning: (morning: number) => void;
  chip: Chip;
  /** The game over's last page, by its morning (`finalMorning`): named for its night in the pager. */
  final?: number | null;
}

export function RecordSheet({ page, mornings, onMorning, chip, final }: RecordSheetProps) {
  if (!page)
    return (
      <>
        <div className={styles.shHead}>
          <span className={styles.title}>On the record</span>
        </div>
        <p className={styles.empty}>
          Nothing on record yet — the first record is written at the end of day 1.
        </p>
      </>
    );
  const at = mornings.indexOf(page.morning);
  const against = page.accusations.some((a) => a.recordCheck);
  const name = (m: number) => `${m === final ? 'Night' : 'Day'} ${m - 1}`;
  return (
    <>
      <div className={styles.shHead}>
        {page.final ? (
          <>
            <span className={styles.title}>Night {page.day}’s record</span>
            <span className={styles.typed}>the game ended at dawn</span>
          </>
        ) : (
          <>
            <span className={styles.title}>Day {page.day}’s record</span>
            <span className={styles.typed}>read at the dawn of day {page.morning}</span>
          </>
        )}
      </div>
      {mornings.length > 1 ? (
        <div className={`${styles.pager} ${styles.rpager}`}>
          <button
            type="button"
            className={styles.pbtn}
            disabled={at <= 0}
            onClick={() => onMorning(mornings[at - 1])}
          >
            ← {name(mornings[Math.max(at - 1, 0)])}
          </button>
          <span className={styles.dots}>
            {mornings.map((m) => (
              <button
                key={m}
                type="button"
                aria-label={`${name(m)}’s record`}
                aria-current={m === page.morning ? 'page' : undefined}
                onClick={() => onMorning(m)}
              >
                <i />
              </button>
            ))}
          </span>
          <button
            type="button"
            className={styles.pbtn}
            disabled={at >= mornings.length - 1}
            onClick={() => onMorning(mornings[at + 1])}
          >
            {name(mornings[Math.min(at + 1, mornings.length - 1)])} →
          </button>
        </div>
      ) : null}
      {/* the game over's last page is the night alone: no morning read its day's summary */}
      {page.final ? null : (
        <>
          <p className={styles.sect}>Claims</p>
          {page.players.length ? (
            <div className={styles.rows}>
              {page.players.map((p) => (
                <Claim key={p.player} player={p} chip={chip} />
              ))}
            </div>
          ) : (
            <p className={styles.none}>No one has claimed a role yet.</p>
          )}
          <p className={styles.sect}>Accusations · day {page.day}</p>
          {page.accusations.length ? (
            page.accusations.map((a, i) => <Accusation key={i} a={a} chip={chip} />)
          ) : (
            <p className={styles.none}>No accusations on day {page.day}.</p>
          )}
        </>
      )}
      {page.nights.length ? (
        <>
          <p className={styles.sect}>
            Night {page.day} ·{' '}
            {page.nights.every((n) => n.mine) ? 'only you' : 'what only each seat learned'}
          </p>
          {page.nights.map((n) => (
            <NightLine key={n.seat} line={n} chip={chip} />
          ))}
        </>
      ) : null}
      {page.final ? null : (
        <p className={styles.legend}>
          {page.checked
            ? '✓ the game record agrees · ✗ the record disagrees or a rule is broken · claims are what players said, not facts'
            : `${against ? '✗ the record disagrees · ' : ''}claims are what players said, not facts; this game’s claims were not checked against the record`}
        </p>
      )}
    </>
  );
}

const cap = (s: string) => (s ? s.charAt(0).toUpperCase() + s.slice(1) : s);
const roleWord = (role: string) =>
  (ROLE_NAME[role] ?? role.replace(/_/g, ' ')).toLowerCase();

/** One player's claims: like a read's row, the claimed role in plain ink, then their lines. */
function Claim({ player: p, chip }: { player: LedgerPlayer; chip: Chip }) {
  const now = currentClaim(p);
  return (
    <div className={styles.claim} data-claim={p.player}>
      {chip(p.player, `${styles.face} ${styles.sm}`)}
      <span className={styles.guess}>
        <small>Seat {seatNumber(p.player)}</small>
        {now ? (
          <b className={now.retracted ? styles.struck : undefined}>{roleWord(now.role)}</b>
        ) : (
          <small>no role claimed</small>
        )}
        {now?.retracted ? <small>withdrawn</small> : null}
      </span>
      {p.roles.length > 1 && p.history ? (
        <p className={styles.chist}>{seatify(p.history)}</p>
      ) : null}
      <Checks list={p.checks} />
      {p.entries.map((e, i) => (
        <Entry key={i} e={e} chip={chip} />
      ))}
    </div>
  );
}

/** A claimed night action (or a plan never reported on), and what the game says of it. */
function Entry({ e, chip }: { e: LedgerEntry; chip: Chip }) {
  const plan = planKind(e);
  const seat = (s: string) =>
    /^player_\d+$/.test(s) ? (
      <span className={styles.seat}>
        {chip(s, `${styles.face} ${styles.xs}`)}Seat {seatNumber(s)}
      </span>
    ) : (
      seatify(s)
    );
  const result = resultWords(e.result);
  return (
    <div className={styles.entry}>
      {plan === 'only' ? (
        <p className={styles.plan}>
          {nightName(e.night)} · said on day {e.said_on_day} they planned to{' '}
          {PLAN_VERB[e.action] ?? e.action} {seat(e.target)}
        </p>
      ) : (
        <p className={styles.eline}>
          <span className={styles.night}>{nightName(e.night)} ·</span>
          {e.action ? (
            <>
              {CLAIM_VERB[e.action] ?? e.action} {seat(e.target)}
              {result ? (
                <>
                  {' '}
                  → <b>{result}</b>
                </>
              ) : null}
            </>
          ) : (
            seatify(`${e.target} ${e.result}`.trim())
          )}
          {plan === 'as-planned' ? <span className={styles.ptag}>as planned</span> : null}
        </p>
      )}
      {e.earlier.map((t, i) => (
        <p key={`earlier-${i}`} className={styles.earlier}>
          earlier: <s>{seatify(t)}</s>
        </p>
      ))}
      {e.also.map((t, i) => (
        <p key={`also-${i}`} className={styles.earlier}>
          also named: {seatify(t)}
        </p>
      ))}
      <Checks list={e.checks} />
      {plan === 'changed' ? (
        <p className={styles.plan}>
          said on day {e.night} they planned to {PLAN_VERB[e.action] ?? e.action}{' '}
          {seat(e.planned!)}
          {e.reason ? <> · reason given: {seatify(e.reason)}</> : null}
        </p>
      ) : null}
    </div>
  );
}

/** The game's checks: ✓ the record agrees, ✗ it disagrees or a rule is broken, else a note. */
function Checks({ list }: { list: readonly LedgerCheck[] }) {
  return list.map((c, i) => (
    <p
      key={i}
      className={`${styles.ck} ${c.fits === true ? styles.ckYes : c.fits === false ? styles.ckNo : styles.ckNote}`}
      data-fits={c.fits === null ? 'note' : String(c.fits)}
    >
      {c.fits === null ? null : (
        <span className={styles.ckm} aria-label={c.fits ? 'Agrees:' : 'Disagrees:'}>
          {c.fits ? '✓' : '✗'}
        </span>
      )}
      {seatify(c.text)}
    </p>
  ));
}

/**
 * A seat's night as the engine recorded it, one line in its words ("Tonight seat 5 was visited
 * by seat 3 and seat 4."): the viewer's own as "You", another's by its seat, the pack's kill
 * once for the pack.
 */
function NightLine({ line, chip }: { line: NightRecordLine; chip: Chip }) {
  const who =
    line.seat === 'wolves' ? (
      line.mine ? (
        'Your pack'
      ) : (
        'The pack'
      )
    ) : line.mine ? (
      'You'
    ) : (
      <span className={styles.seat}>
        {chip(line.seat, `${styles.face} ${styles.xs}`)}Seat {seatNumber(line.seat)}
      </span>
    );
  return (
    <div className={styles.entry} data-night-record={line.seat}>
      <p className={styles.eline}>
        <span className={styles.night}>{who} ·</span>
        {seatify(line.outcome)}
      </p>
    </div>
  );
}

/** One accusation, compact: who → whom, the reasoning in two lines; opened, all of it. */
function Accusation({ a, chip }: { a: SummaryAccusation; chip: Chip }) {
  const [open, setOpen] = useState(false);
  const sm = `${styles.face} ${styles.sm}`;
  const more = a.defense ? 'Defence' : a.disputedBy ? 'Disputed' : null;
  return (
    <div className={styles.acc} data-open={open || undefined}>
      <header>
        <span className={styles.faces}>
          {a.accusers.map((p) => (
            <span key={p}>{chip(p, sm)}</span>
          ))}
        </span>
        <span aria-hidden="true">→</span>
        {chip(a.target, sm)}
        <span>
          {a.accusers.map((p) => `Seat ${seatNumber(p)}`).join(', ')} → Seat{' '}
          {seatNumber(a.target)}
        </span>
      </header>
      <button
        type="button"
        className={styles.areason}
        aria-expanded={open}
        onClick={() => setOpen((o) => !o)}
      >
        <span>{cap(seatify(a.reasoning))}</span>
      </button>
      {a.recordCheck ? (
        <p className={`${styles.ck} ${styles.ckNo}`} data-fits="false">
          <span className={styles.ckm} aria-label="Disagrees:">
            ✗
          </span>
          Against the record: {seatify(a.recordCheck)}
        </p>
      ) : null}
      {more ? (
        <button
          type="button"
          className={styles.adef}
          aria-expanded={open}
          onClick={() => setOpen((o) => !o)}
        >
          {more} {open ? '▾' : '▸'}
        </button>
      ) : null}
      {open && a.defense ? (
        <p className={styles.def}>
          <b>Defence:</b> {seatify(a.defense)}
        </p>
      ) : null}
      {open && a.disputedBy ? (
        <p className={styles.def}>
          <b>Disputed:</b> {seatify(a.disputedBy)}
        </p>
      ) : null}
    </div>
  );
}
