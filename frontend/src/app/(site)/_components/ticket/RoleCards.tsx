/**
 * The solo ticket's role choice (ticket-office mockup, "Your role"): the only cards on the
 * page, because cards mean roles. Face down is "dealt at random"; each face carries the role's
 * sigil, its name and the role kit's felt figure, banded in its faction's colour. The note under
 * the row says what the chosen role does at night, in the card's own words (`CARD_TEXT`).
 *
 * The cards are the deal's pool of twelve (`PoolRole`); villager and wolf are retired from it.
 * They sit as the deal does: the eight roles every game deals, then the lone killer's pair and
 * the neutral's pair on a row of their own, since a game deals one of each pair (or the one the
 * player chose). The cards are a radio group: the arrow keys move the choice, as the landing's
 * role hand does.
 *
 * Solo only: rooms always deal at random (`NewRoom` has no role field), so the room ticket
 * never renders this.
 */
import { useId } from 'react';
import { CARD_TEXT } from '@/stage/card-text';
import { roleFigure } from '@/stage/paint/role-kit';
import { factionOf } from '@/stage/roles';
import { BackArt } from '@/stage/instruments/CardBackArt';
import { Sigil } from '@/stage/instruments/Sigil';
import type { PoolRole } from '@/types/contracts';
import classes from './Ticket.module.css';

/** The eight seats every game deals (`FIXED_SEATS`, Agents/schemas/roles.py). */
const FIXED: PoolRole[] = [
  'investigator',
  'sentinel',
  'trailseer',
  'vigilante',
  'sigilist',
  'healer',
  'chanteuse',
  'illusionist',
];

/** The two drawn seats: a game deals one role of each pair, or the one the player chose. */
export const DRAWN: readonly { side: string; roles: PoolRole[] }[] = [
  { side: 'Lone killer', roles: ['serial_killer', 'necromancer'] },
  { side: 'Neutral', roles: ['speculator', 'fortune_teller'] },
];

/** The castable roles: the town's six, the pack's two, the lone killers, the neutrals. */
export const ROLES: PoolRole[] = [...FIXED, ...DRAWN.flatMap((d) => d.roles)];

/** A drawn role's seat as a card prints it ("Lone killer, drawn"); undefined for a fixed role. */
export function drawnSeat(role: PoolRole): string | undefined {
  const d = DRAWN.find((x) => x.roles.includes(role));
  return d ? `${d.side}, drawn` : undefined;
}

/** The radio group's order: face down first, then the pool. */
const CHOICES: (PoolRole | null)[] = [null, ...ROLES];

const STEP: Record<string, number> = {
  ArrowRight: 1,
  ArrowDown: 1,
  ArrowLeft: -1,
  ArrowUp: -1,
};

/** The pack's roles: their packmate is always an agent. */
const PACK: readonly PoolRole[] = ['chanteuse', 'illusionist'];

export function RoleCards({
  value,
  onChange,
  labelledBy,
}: {
  value: PoolRole | null;
  onChange: (role: PoolRole | null) => void;
  labelledBy: string;
}) {
  const text = value ? CARD_TEXT[value] : null;
  const dealId = useId();

  const card = (role: PoolRole) => (
    <button
      key={role}
      type="button"
      role="radio"
      className={classes.card}
      data-faction={factionOf(role) ?? undefined}
      data-choice={role}
      aria-checked={value === role}
      aria-label={
        drawnSeat(role) ? `${CARD_TEXT[role].name}, a drawn seat` : CARD_TEXT[role].name
      }
      tabIndex={value === role ? 0 : -1}
      onClick={() => onChange(role)}
    >
      <span className={classes.cardIn}>
        <span className={classes.cardHead}>
          <Sigil role={role} strokeWidth={3.2} className={classes.cardSigil} />
          {CARD_TEXT[role].name}
        </span>
        <span
          className={classes.cardFig}
          aria-hidden="true"
          dangerouslySetInnerHTML={{ __html: roleFigure(role) }}
        />
      </span>
    </button>
  );

  return (
    <>
      <div
        className={classes.cards}
        role="radiogroup"
        aria-labelledby={labelledBy}
        aria-describedby={dealId}
        onKeyDown={(e) => {
          const step = STEP[e.key];
          if (!step) return;
          e.preventDefault();
          const i = CHOICES.indexOf(value) + step;
          const next = CHOICES[(i + CHOICES.length) % CHOICES.length];
          onChange(next);
          e.currentTarget
            .querySelector<HTMLElement>(`[data-choice="${next ?? 'random'}"]`)
            ?.focus();
        }}
      >
        <button
          type="button"
          role="radio"
          className={`${classes.card} ${classes.cardBack}`}
          data-choice="random"
          aria-checked={value === null}
          aria-label="Dealt at random"
          tabIndex={value === null ? 0 : -1}
          onClick={() => onChange(null)}
        >
          <span className={classes.cardIn}>
            <span className={classes.backArt}>
              <BackArt />
            </span>
            <span className={classes.backWords}>
              Dealt at
              <br />
              random
            </span>
          </span>
        </button>
        {FIXED.map(card)}
        <div className={classes.drawnRow}>
          {DRAWN.map((d) => (
            <div key={d.side} className={classes.drawn}>
              <span className={classes.drawnLabel} aria-hidden="true">
                {drawnSeat(d.roles[0])}
              </span>
              <div className={classes.drawnCards}>{d.roles.map(card)}</div>
            </div>
          ))}
        </div>
      </div>
      <p id={dealId} className={classes.note}>
        Eight roles are always dealt. The lone killer and the neutral seat are drawn; pick
        one of those and the draw follows you.
      </p>
      <p className={classes.roleNote} aria-live="polite">
        {text ? (
          <>
            <b>{text.name}.</b> {text.night}
            {value && PACK.includes(value) ? ' Your packmate will be an agent.' : ''}
          </>
        ) : (
          <>
            <b>Dealt at random</b>, like everyone else&rsquo;s, from the table&rsquo;s cast.
          </>
        )}
      </p>
    </>
  );
}
