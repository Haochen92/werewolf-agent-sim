'use client';

/**
 * What the stage says in words when nobody is at the stand: "Nine at the table", "Seat 3 was
 * attacked in the night", "You are the healer". A dark glass box at the foot of the stage, in
 * the speech box's place, with the seat's chip or the role's sigil in its header; and, for a
 * seated human, their card at rest beside it ("your card").
 *
 * Every line here is the client's: nothing on the wire narrates the deal or reads the morning
 * aloud. `arrive` fades the box in when a beat plays forward; at rest it is simply there.
 */
import { motion } from 'motion/react';
import type { CSSProperties, ReactNode } from 'react';
import { SPRITES, type Character } from '@/assets/manifest';
import { ChipSprite } from '../cast/ChipSprite';
import { useMotionScale } from '../motion';
import { CARD_TEXT } from '../card-text';
import { roleAvatar } from '../paint/role-kit';
import { factionOf } from '../roles';
import { bandFoot, geometry, type Hud } from '../units';
import { Sigil } from './Sigil';
import styles from './Notice.module.css';

/** The band along the foot of the stage the boxes sit in, clear of the wing (and the side slot). */
export function NoticeZone({
  hud,
  side = false,
  aside = false,
  children,
}: {
  hud: Hud;
  /** The side slot is open: the zone stops short of it. */
  side?: boolean;
  /**
   * The side slot holds something that stops at the rail (the film, or the drawer on a
   * prompt): on a phone, where the box's words are larger and it rises past the rail, the zone
   * stops short of it too (see `--grown`); at full size it keeps the band.
   */
  aside?: boolean;
  children: ReactNode;
}) {
  const g = geometry(hud, side);
  const inset = 22.4;
  const right = side ? 1600 - g.wingN - g.room + inset : inset;
  const s = geometry(hud, true);
  return (
    <div
      className={styles.zone}
      style={
        {
          left: g.wingN + inset,
          bottom: bandFoot(hud, 19.2),
          '--right': `${right}px`,
          '--aside': aside ? `${1600 - s.wingN - s.room + inset}px` : undefined,
        } as CSSProperties
      }
    >
      {children}
    </div>
  );
}

export interface NoticeProps {
  /** The header's lead: a seat's chip, or a role's sigil. */
  chip?: Character | null;
  sigil?: string | null;
  title: ReactNode;
  /** Small words after the title. */
  aside?: ReactNode;
  /** The X-ray's tag, in its verdigris (the prop keeps the film's old name): "Only seat 4". */
  aqua?: string | null;
  children?: ReactNode;
  wide?: boolean;
  arrive?: boolean;
  /** Arrival delay, seconds. */
  delay?: number;
  /**
   * The HUD's walnut board (the speech box's material) in place of the glass: a notice the
   * viewer answers, the replay's stops (owner, 2026-09-30).
   */
  walnut?: boolean;
  /** The ways on, under the words: `NoticeButton`s. */
  actions?: ReactNode;
}

export function Notice({
  chip,
  sigil,
  title,
  aside,
  aqua,
  children,
  wide,
  arrive = false,
  delay = 0,
  walnut = false,
  actions,
}: NoticeProps) {
  const k = useMotionScale();
  const f = factionOf(sigil);
  const cls = [
    styles.box,
    wide ? styles.wide : '',
    aqua ? styles.xr : '',
    walnut ? styles.walnut : '',
  ]
    .filter(Boolean)
    .join(' ');
  return (
    <motion.div
      className={cls}
      style={
        walnut
          ? ({ '--board': `url(${SPRITES.textures.walnut.src})` } as CSSProperties)
          : undefined
      }
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: delay * k }}
    >
      <header className={styles.head}>
        {chip ? (
          <span className={styles.chip}>
            <ChipSprite character={chip} />
          </span>
        ) : null}
        {sigil ? (
          <Sigil
            role={sigil}
            variant="felt"
            className={`${styles.sigil} ${f ? styles[`c-${f}`] : ''}`}
          />
        ) : null}
        <strong>{title}</strong>
        {aside ? <span>{aside}</span> : null}
        {aqua ? <span className={styles.aqua}>{aqua}</span> : null}
      </header>
      {children ? <div className={styles.body}>{children}</div> : null}
      {actions ? <div className={styles.actions}>{actions}</div> : null}
    </motion.div>
  );
}

/**
 * A way on from a notice ("Watch them all ▶", "End the night →", "← Back to the night"): a
 * small walnut plaque with a brass edge, the strip's material. `lead` is the one the notice
 * leads with, its edge brighter.
 */
export function NoticeButton({
  children,
  onPress,
  lead = false,
}: {
  children: ReactNode;
  onPress?: () => void;
  lead?: boolean;
}) {
  return (
    <button
      type="button"
      className={lead ? `${styles.go} ${styles.lead}` : styles.go}
      onClick={onPress}
      data-stop-button
    >
      {children}
    </button>
  );
}

/**
 * The seated human's card, at rest beside the box. The button only reports the press. Once the
 * seat is out of the game its card has gone to the wing, and the button says so (`gone`).
 */
export function CardButton({
  role,
  onOpen,
  gone = false,
}: {
  role: string;
  onOpen?: () => void;
  gone?: boolean;
}) {
  const f = factionOf(role);
  return (
    <button
      type="button"
      className={`${styles.card} ${f ? styles[`r-${f}`] : ''} ${gone ? styles.gone : ''}`}
      onClick={onOpen}
      aria-label={`Your card: ${CARD_TEXT[role]?.name ?? role}`}
    >
      <span className={styles.av} dangerouslySetInnerHTML={{ __html: roleAvatar(role) }} />
      <em>{gone ? 'on the wing' : 'your card'}</em>
    </button>
  );
}

const CAST_ORDER = [
  'villager',
  'healer',
  'investigator',
  'vigilante',
  'wolf',
  'serial_killer',
];
const PLURAL: Record<string, string> = {
  villager: 'villagers',
  healer: 'healers',
  investigator: 'investigators',
  vigilante: 'vigilantes',
  wolf: 'wolves',
  serial_killer: 'serial killers',
};

/** The cast counts, as the plate reads them: "3 villagers, 1 healer, …", each with its sigil. */
export function CastLine({ counts }: { counts: Record<string, number> }) {
  const roles = [
    ...CAST_ORDER.filter((r) => counts[r]),
    ...Object.keys(counts).filter((r) => !CAST_ORDER.includes(r) && counts[r]),
  ];
  return (
    <div className={styles.cast}>
      {roles.map((r) => {
        const f = factionOf(r);
        const n = counts[r];
        return (
          <span key={r} className={f ? styles[`c-${f}`] : undefined}>
            <b>{n}</b>
            <Sigil role={r} variant="felt" small />
            {n > 1 ? PLURAL[r] : (CARD_TEXT[r]?.name ?? r).toLowerCase()}
          </span>
        );
      })}
    </div>
  );
}

const WORDS = ['No', 'One', 'Two', 'Three', 'Four', 'Five'];

/** The vigilante's caps: one red cap per bullet left. */
export function Caps({ n }: { n: number }) {
  return (
    <div className={styles.caps}>
      {WORDS[n] ?? n} {n === 1 ? 'cap' : 'caps'} in the popgun
      {Array.from({ length: n }, (_, i) => (
        <i key={i} />
      ))}
    </div>
  );
}

/**
 * The pack chat as it opens at the deal: the game master's line naming the packmate, and the
 * place to write. A placeholder until the pack's chat is built with its room; the input is
 * inert here.
 */
export function PackChat({
  mate,
  character,
  arrive = false,
}: {
  mate: number;
  character: Character;
  arrive?: boolean;
}) {
  const k = useMotionScale();
  return (
    <motion.div
      className={`${styles.box} ${styles.wide} ${styles.pack}`}
      initial={arrive ? { opacity: 0 } : false}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.4 * k, delay: 0.7 * k }}
    >
      <header className={styles.head}>
        <span className={styles.pk}>Pack</span>
        <strong>The wolf chat</strong>
        <span>only the two of you</span>
      </header>
      <div className={styles.body}>
        <div className={styles.line}>
          <b>Game master</b>
          <span>
            Your packmate is seat {mate}{' '}
            <span className={styles.chip}>
              <ChipSprite character={character} />
            </span>
            . You hunt together at night.
          </span>
        </div>
        <div className={styles.input} aria-disabled="true">
          Say something to your packmate… (the pack talks at night; this stays open)
        </div>
      </div>
    </motion.div>
  );
}
