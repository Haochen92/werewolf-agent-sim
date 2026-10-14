'use client';

/**
 * A role's card, the briefing its agent is given: the front is the role (its sigil, felt figure,
 * line and side), the back is the briefing (by day, at night, how you win), in the card's own
 * words (`CARD_TEXT`), inked in its side's colour. The landing shows one, the guide a row per
 * side. The card is the only place a role is written up, so it turns over rather than laying the
 * briefing out beside it.
 *
 * Controlled: the holder keeps which face is up, so a switch beside the card (`BriefingsSwitch`)
 * and a tap on the card stay in step. With a mouse the card tilts on hover to show it turns, but
 * not after a click until the pointer leaves, so a card just turned never hangs half-turned.
 */
import { useState, type CSSProperties } from 'react';
import { CARD_TEXT } from '@/stage/card-text';
import { roleFigure } from '@/stage/paint/role-kit';
import { FACTION_NAME, factionOf } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import type { PoolRole } from '@/types/contracts';
import classes from './RoleCard.module.css';

/** "Two of them,\nand neither is Grandma." with the kit's line breaks kept. */
function Lines({ text }: { text: string }) {
  const parts = text.split('\n');
  return parts.map((p, i) => (
    <span key={i}>
      {p}
      {i < parts.length - 1 ? <br /> : null}
    </span>
  ));
}

export function RoleCard({
  role,
  turned,
  onTurn,
  delay = 0,
  className,
}: {
  role: PoolRole;
  turned: boolean;
  onTurn: (turned: boolean) => void;
  /** ms before this card turns: a row turned by one switch turns card after card. */
  delay?: number;
  className?: string;
}) {
  const [settled, setSettled] = useState(false);
  const text = CARD_TEXT[role];
  const faction = factionOf(role) ?? 'villagers';

  return (
    <button
      type="button"
      className={className ? `${classes.card} ${className}` : classes.card}
      data-faction={faction}
      data-turned={turned || undefined}
      data-settled={settled || undefined}
      aria-pressed={turned}
      aria-label={`${text.name} card, turn it over`}
      style={{ '--turn-delay': `${delay}ms` } as CSSProperties}
      onClick={() => {
        setSettled(true);
        onTurn(!turned);
      }}
      onPointerLeave={() => setSettled(false)}
    >
      <span className={`${classes.face} ${classes.front}`} aria-hidden={turned}>
        <span className={classes.frame} />
        <span className={classes.hdr}>
          <span className={classes.name}>{text.name}</span>
          <Sigil role={role} strokeWidth={2.4} className={classes.sigil} />
        </span>
        <span
          className={classes.portrait}
          dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
        />
        <span className={classes.desc}>
          <Lines text={text.line} />
        </span>
        <span className={classes.fac}>
          <span>{FACTION_NAME[faction]}</span>
          <FactionMark faction={faction} format="badge" small className={classes.seal} />
        </span>
      </span>
      <span className={`${classes.face} ${classes.back}`} aria-hidden={!turned}>
        <span className={classes.frame} />
        <span className={classes.hdr}>
          <span className={classes.name}>{text.name}</span>
          <span className={classes.kind}>the briefing</span>
        </span>
        <span className={classes.brief}>
          <span className={classes.para}>
            <em>By day</em>
            {text.day}
          </span>
          <span className={classes.para}>
            <em>At night</em>
            {text.night}
          </span>
          <span className={classes.para}>
            <em>How you win</em>
            {text.win}
          </span>
        </span>
        <span className={classes.fac}>
          <span>{FACTION_NAME[faction]}</span>
          <FactionMark faction={faction} format="badge" small className={classes.seal} />
        </span>
      </span>
    </button>
  );
}
