'use client';

/**
 * The roles on the landing ("The roles"): the pool's twelve sigils as the picker, one large card
 * under them that turns over to the briefing its agent is given, and the way to the guide. The
 * picker groups the sides as the deal does, each under its felt mark and ringed in its colour;
 * the sigils carry no names (the card does). The card's face survives a change of role, so a
 * visitor who turned it can read briefing after briefing.
 */
import { useState } from 'react';
import Link from 'next/link';
import { Button } from '@/components/site';
import { CARD_TEXT } from '@/stage/card-text';
import { FACTION_NAME } from '@/stage/roles';
import { FactionMark } from '@/stage/instruments/FactionMark';
import { Sigil } from '@/stage/instruments/Sigil';
import type { PoolRole } from '@/types/contracts';
import { BriefingsSwitch } from '../BriefingsSwitch';
import { RoleCard } from '../RoleCard';
import { ARROW_STEP, ROLES, SIDES } from '../sides';
import classes from './RoleHand.module.css';

export function RoleHand() {
  const [role, setRole] = useState<PoolRole>('chanteuse');
  const [turned, setTurned] = useState(false);

  return (
    <div className={classes.hand}>
      <div
        className={classes.pick}
        role="radiogroup"
        aria-label="Roles"
        onKeyDown={(e) => {
          const step = ARROW_STEP[e.key];
          if (!step) return;
          e.preventDefault();
          const i = ROLES.indexOf(role) + step;
          const next = ROLES[(i + ROLES.length) % ROLES.length];
          setRole(next);
          e.currentTarget.querySelector<HTMLElement>(`[data-role="${next}"]`)?.focus();
        }}
      >
        {SIDES.map((side) => (
          <div key={side.faction} className={classes.side} data-faction={side.faction}>
            <span className={classes.mark} title={FACTION_NAME[side.faction]}>
              <FactionMark faction={side.faction} format="mark" />
            </span>
            {side.roles.map((r) => (
              <button
                key={r}
                type="button"
                role="radio"
                aria-checked={r === role}
                aria-label={CARD_TEXT[r].name}
                title={CARD_TEXT[r].name}
                tabIndex={r === role ? 0 : -1}
                data-role={r}
                className={classes.disc}
                onClick={() => setRole(r)}
              >
                <Sigil role={r} strokeWidth={2.6} className={classes.discSigil} />
              </button>
            ))}
          </div>
        ))}
      </div>

      <div className={classes.card}>
        <RoleCard role={role} turned={turned} onTurn={setTurned} />
      </div>

      <div className={classes.under}>
        <BriefingsSwitch checked={turned} onChange={setTurned} />
        <Button component={Link} href="/guide" size="sm">
          Gameplay guide &rarr;
        </Button>
      </div>
    </div>
  );
}
