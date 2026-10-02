'use client';

/**
 * The epilogue: what the finished game taught, as the case's closing spread brought down over
 * the whole stage (handoff §4.10, bench 73; in the case file's manila and typed paper since
 * 2026-09-30, it was the X-ray's blue-black film). The agents' observations were private all
 * game; after the game is over the X-ray is everyone's, so every viewer gets this sheet.
 *
 * - Down the left, one file tab per role (the wire files observations by role, not seat): its
 *   sigil, the chips of the seats that held it, "won" on the winning side, and a pip per
 *   verdict as a tally.
 * - Each row carries its verdict as a mark (✓ ✗ ± ?), so it never rests on colour alone.
 * - On the right, that role's rows under the phase they came from (the discussion, the vote,
 *   the night). Each row shows only its scenario, clamped to two lines, with a chevron and
 *   "open"; opened, it adds what the agent did and how it went, with the verdict stamped
 *   beside the outcome, because a verdict is on the outcome.
 * - Along the bottom, the lessons kept (the strategy points) as index cards, or "None from this
 *   game" when there are none.
 *
 * Tabs and rows are the viewer's own to click; nothing here changes the beat. Played, the
 * sheet comes down 0.6 s after 0.5 s (bench 73 `plateIn`) over a stage dimmed 0.5 s after 0.3 s.
 */
import { motion } from 'motion/react';
import { useState, type CSSProperties } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import type { MemoryExtracted } from '@/types/contracts';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { useSmall } from '../Stage';
import { ROLE_NAME, factionOf, seatNumber, seatify, type Faction } from '../roles';
import { bandFoot, geometry, type Hud } from '../units';
import {
  PHASE_NAME,
  byPhase,
  ledgerTabs,
  stripVerdict,
  type ActionPhase,
  type VerdictKind,
} from './ledger';
import { Sigil } from './Sigil';
import { VerdictMark } from './VerdictMark';
import styles from './Ledger.module.css';

/** The verdict as the case file stamps it (its Findings stamp the same marks). */
const STAMP: Record<VerdictKind, string> = {
  worked: 'Worked',
  cost: 'Cost',
  mixed: 'Mixed',
  unclear: 'Unclear',
};
/** The stamps' worn ink: a still mask tile, as the case file's. */
const INK_TEX = { '--ink-tex': `url(${SPRITES.textures.ink.src})` } as CSSProperties;

/** Each phase's small line icon (16×16), for the headers the rows are grouped under; the case
 * file's Findings index uses the same. */
export const PHASE_ICON: Record<ActionPhase, React.ReactNode> = {
  day_discussion: <path d="M2 3h12v8H7l-3 3v-3H2z" />,
  day_vote: (
    <>
      <circle cx="8" cy="8" r="6" />
      <circle cx="8" cy="8" r="2.4" />
    </>
  ),
  night_action: <path d="M10 2a6 6 0 1 0 4 10 5 5 0 0 1-4-10z" />,
};

export interface LedgerProps {
  hud: Hud;
  /** `memory_extracted`; null for a game played without memory (the sheet says so). */
  extracted: MemoryExtracted | null;
  /** Seat → role: whose chips go on each tab. */
  roles: Record<string, string>;
  /** Who plays which seat; index 0 = player_1. */
  cast: readonly Character[];
  winner: Faction | null;
  /** Come down (played); at rest it is simply there. */
  arrive?: boolean;
  /** The role whose tab is open first (default: the winning side's, else the first). */
  tab?: string;
  /** A row open from the start, by its place in the extraction. */
  open?: number | null;
}

export function Ledger({
  hud,
  extracted,
  roles,
  cast,
  winner,
  arrive = false,
  tab,
  open = null,
}: LedgerProps) {
  const k = useMotionScale();
  // a phone: the ledger is simply there (three-quarters of the stage fading in is a full-stage
  // repaint a frame; build log §8.7)
  const small = useSmall();
  const g = geometry(hud);
  const inset = 35.2;
  const box = {
    left: g.wingN + inset,
    right: inset,
    top: inset,
    bottom: bandFoot(hud, inset),
  };
  const tabs = extracted ? ledgerTabs(extracted, roles) : [];
  const first =
    tabs.find((t) => t.role === tab) ??
    tabs.find((t) => factionOf(t.role) === winner) ??
    tabs[0];
  const [current, setCurrent] = useState(first?.role ?? '');
  const [opened, setOpened] = useState<number | null>(open);
  const shown = tabs.find((t) => t.role === current) ?? first;
  const kept = extracted?.strategy_points ?? [];

  const veil = (
    <motion.div
      className={styles.veil}
      initial={arrive && !small ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 * k, delay: 0.3 * k }}
    />
  );
  const sheet = (children: React.ReactNode) => (
    <motion.section
      className={styles.ledger}
      style={{ ...box, ...INK_TEX }}
      aria-label="What the game taught"
      data-ledger=""
      initial={arrive && !small ? { opacity: 0, y: 24 } : false}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.6 * k, delay: 0.5 * k, ease: [0.3, 0.8, 0.4, 1] }}
    >
      {children}
    </motion.section>
  );

  if (!extracted)
    return (
      <>
        {veil}
        {sheet(
          <>
            <header className={styles.head}>
              <strong>What the game taught</strong>
            </header>
            <p className={styles.none}>No memory was kept.</p>
          </>,
        )}
      </>
    );

  const n = extracted.observations.length;
  return (
    <>
      {veil}
      {sheet(
        <>
          <header className={styles.head}>
            <strong>What the game taught</strong>
            <span>each role’s own account of its play, before any of it is kept</span>
            <span className={styles.count}>
              <b>{n}</b> observation{n === 1 ? '' : 's'} · <b>{kept.length || 'no'}</b>{' '}
              lesson
              {kept.length === 1 ? '' : 's'} kept
            </span>
          </header>

          <nav className={styles.tabs} aria-label="Roles">
            {tabs.map((t) => {
              const f = factionOf(t.role);
              return (
                <button
                  key={t.role}
                  type="button"
                  className={`${styles.tab} ${f ? styles[`c-${f}`] : ''}`}
                  aria-pressed={t.role === shown?.role}
                  onClick={() => {
                    setCurrent(t.role);
                    setOpened(null);
                  }}
                  data-tab={t.role}
                >
                  <Sigil role={t.role} variant="felt" className={styles.sigil} />
                  <span className={styles.name}>
                    {ROLE_NAME[t.role] ?? t.role}
                    {t.seats.map((s) => {
                      const c = cast[seatNumber(s) - 1];
                      return (
                        <span
                          key={s}
                          className={styles.chip}
                          title={`Seat ${seatNumber(s)}`}
                        >
                          {c ? <ChipSprite character={c} /> : null}
                        </span>
                      );
                    })}
                    {f && f === winner ? <span className={styles.won}>won</span> : null}
                  </span>
                  <span
                    className={styles.pips}
                    aria-label={`${t.tally.worked} worked, ${t.tally.mixed} mixed, ${t.tally.cost} cost, ${t.tally.unclear} unclear`}
                  >
                    {t.pips.map((p, i) => (
                      <i key={i} className={styles[p]} />
                    ))}
                  </span>
                </button>
              );
            })}
          </nav>

          <div className={styles.rows}>
            {shown
              ? byPhase(shown.rows).flatMap(({ phase, rows }) => [
                  <div key={phase} className={styles.phase}>
                    <svg viewBox="0 0 16 16" aria-hidden="true">
                      {PHASE_ICON[phase]}
                    </svg>
                    {PHASE_NAME[phase]}
                    <i />
                    <span>{rows.length}</span>
                  </div>,
                  ...rows.map((r) => {
                    const isOpen = opened === r.index;
                    const toggle = () => setOpened(isOpen ? null : r.index);
                    return (
                      <div
                        key={r.index}
                        className={isOpen ? `${styles.row} ${styles.open}` : styles.row}
                        role="button"
                        tabIndex={0}
                        aria-expanded={isOpen}
                        data-row={r.index}
                        onClick={toggle}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            toggle();
                          }
                        }}
                      >
                        <div className={styles.rowHead}>
                          <span className={styles.chev}>
                            <svg viewBox="0 0 16 16" aria-hidden="true">
                              <path d="M6 3l5 5-5 5" />
                            </svg>
                          </span>
                          {/* the verdict as a mark, not colour alone (colour-blind safe) */}
                          <VerdictMark
                            kind={r.verdict}
                            className={`${styles.vmark} ${styles[`m-${r.verdict}`] ?? ''}`}
                          />
                          <span className={styles.label}>Scenario</span>
                          <div className={styles.situation}>{seatify(r.obs.situation)}</div>
                          <span className={styles.more}>{isOpen ? 'close' : 'open'}</span>
                        </div>
                        {isOpen ? (
                          <div className={styles.body}>
                            <div>
                              <b>What it did</b>
                              <p>{seatify(r.obs.approach)}</p>
                            </div>
                            <div
                              className={`${styles.went} ${styles[`v-${r.verdict}`] ?? ''}`}
                            >
                              <span
                                className={`${styles.stamp} ${styles[`t-${r.verdict}`] ?? ''}`}
                                data-verdict={r.verdict}
                              >
                                <VerdictMark kind={r.verdict} />
                                {STAMP[r.verdict]}
                              </span>
                              <div>
                                <b>How it went</b>
                                <p>{seatify(stripVerdict(r.obs.outcome))}</p>
                              </div>
                            </div>
                          </div>
                        ) : null}
                      </div>
                    );
                  }),
                ])
              : null}
          </div>

          <div className={styles.kept}>
            <strong>Lessons kept</strong>
            {kept.length ? (
              kept.map((l, i) => (
                <div key={i} className={styles.slip}>
                  <span className={styles.mk}>
                    {ROLE_NAME[l.perspective] ?? l.perspective} ·{' '}
                    {PHASE_NAME[l.action_phase].toLowerCase()}
                  </span>
                  <span>
                    <b>When</b> {seatify(l.situation)}
                  </span>
                  <span>→</span>
                  <span>
                    <b>Do</b> {seatify(l.action)}
                  </span>
                </div>
              ))
            ) : (
              <span>None from this game.</span>
            )}
          </div>
        </>,
      )}
    </>
  );
}
