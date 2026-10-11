'use client';

/**
 * The roles, one card at a time (the landing's "Who's at the table", v2 picker): a row of the
 * pool's twelve sigils picks the role, and the card below turns over on a tap to show its back, the
 * briefing its agent is given (by day, at night, how it wins). The card is the ticket office's
 * role card at section size: the same sigil, felt figure and words (`CARD_TEXT`), inked in its
 * side's colour, the side's badge as the seal by its name. The picker sits as the sides do: the
 * town's six on one row, then the wolves, the lone killers and the neutrals; a drawn role's card
 * says on its side strip that its seat is drawn.
 */
import { useState } from 'react';
import { CARD_TEXT } from '@/stage/card-text';
import { roleFigure } from '@/stage/paint/role-kit';
import { FACTION_NAME, factionOf } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import type { PoolRole } from '@/types/contracts';
import { ROLES, drawnSeat } from '../ticket/RoleCards';
import classes from './RoleHand.module.css';

const STEP: Record<string, number> = {
  ArrowRight: 1,
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowUp: -1,
};

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

export function RoleHand() {
  const [role, setRole] = useState<PoolRole>('chanteuse');
  const [turned, setTurned] = useState(false);
  const text = CARD_TEXT[role];
  const faction = factionOf(role) ?? 'villagers';

  const choose = (r: PoolRole) => {
    setRole(r);
    setTurned(false);
  };

  return (
    <div className={classes.hand}>
      <div
        className={classes.pick}
        role="radiogroup"
        aria-label="Roles"
        onKeyDown={(e) => {
          const step = STEP[e.key];
          if (!step) return;
          e.preventDefault();
          const i = ROLES.indexOf(role) + step;
          const next = ROLES[(i + ROLES.length) % ROLES.length];
          choose(next);
          e.currentTarget.querySelector<HTMLElement>(`[data-role="${next}"]`)?.focus();
        }}
      >
        {ROLES.map((r) => (
          <span key={r} className={classes.pickSlot}>
            {r === 'chanteuse' ? (
              <span className={classes.rowBreak} aria-hidden="true" />
            ) : null}
            {r === 'serial_killer' || r === 'speculator' ? (
              <span className={classes.gap} aria-hidden="true" />
            ) : null}
            <button
              type="button"
              role="radio"
              aria-checked={r === role}
              aria-label={CARD_TEXT[r].name}
              title={CARD_TEXT[r].name}
              tabIndex={r === role ? 0 : -1}
              data-role={r}
              data-faction={factionOf(r) ?? undefined}
              className={classes.sigilButton}
              onClick={() => choose(r)}
            >
              <Sigil role={r} strokeWidth={2.6} className={classes.pickSigil} />
            </button>
          </span>
        ))}
      </div>

      <button
        type="button"
        className={classes.card}
        data-faction={faction}
        data-turned={turned || undefined}
        aria-pressed={turned}
        aria-label={`${text.name} card, turn to read the briefing`}
        onClick={() => setTurned((t) => !t)}
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
            <span>{drawnSeat(role) ?? FACTION_NAME[faction]}</span>
            <FactionMark faction={faction} format="badge" small className={classes.seal} />
          </span>
          <span className={classes.hint}>Turn the card</span>
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
            <span>Summarised from what the agent is told</span>
            <span className={classes.seal} />
          </span>
          <span className={classes.hint}>Turn back</span>
        </span>
      </button>
      <p className={classes.turnHint}>
        Pick a role, then tap its card to read the briefing its agent is given.
      </p>
    </div>
  );
}
